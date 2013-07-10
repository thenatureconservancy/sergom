#########################################################################################
## Script name:     sergom_modelGrowthModules.py
## Description:     Runs Sergom modeling routine; customized for Arizona              
#########################################################################################
import sys, string, os, time

#----------------------------------------------------------------------------------------
def neighborhoodDensity(gp, houseDensWorkspace, decade, thresholdUrban, thresholdSuburban, thresholdExurban, delTemp):
    print ('1. '+time.ctime()+ ' Aggregating ' + decade)
    blockHousingDensity = houseDensWorkspace + '/hd_' + decade
##    neighborDens = houseDensWorkspace + '/nghDens' + decade    
##    gp.Aggregate_sa(blockHousingDensity, neighborDens, "5", "MEAN", "EXPAND", "DATA")
##    
##    desc = gp.Describe
##    gp.Extent = desc(neighborDens).Extent
##    gp.CellSize = desc(neighborDens).MeanCellWidth
    
    print ('2. Focal stats ' + decade)
    neighborDensAvg = houseDensWorkspace + '/nghDnsAvg' + decade    
##    gp.FocalStatistics_sa(neighborDens, neighborDensAvg, "Circle 5 CELL", "MEAN", "DATA") #Uncomment this if using step 1 above
    gp.FocalStatistics_sa(blockHousingDensity, neighborDensAvg, "Circle 8 CELL", "MEAN", "DATA")
       
    print ('3. Reclass ' + decade)
    neighborDensClass = houseDensWorkspace + '/nghDnsCls' + decade    
    gp.Reclassify_sa(neighborDensAvg, 'VALUE', '0 ' +str(thresholdExurban)+ ' 4;' +str(thresholdExurban)+ ' ' +str(thresholdSuburban)+ ' 3;' +str(thresholdSuburban)+ ' ' +str(thresholdUrban)+ ' 2;' +str(thresholdUrban)+ ' 999999 1;', neighborDensClass, "DATA")

    if delTemp == 'yes':
        try:
            print ('deleting temp layers')
            gp.delete(neighborDensAvg)
        except:
            print ('trouble deleting layers')
            print ('4. Finished ' + decade)
    else:
        print ('4. Finished ' + decade)
    return neighborDensClass

#----------------------------------------------------------------------------------------
def distanceFromUrbanClasses(gp, houseDensWorkspace, decade, roadsTravelTimeRaster, urbanPatchSize, delTemp):  
    desc = gp.Describe
    gp.Extent = desc(roadsTravelTimeRaster).Extent
    gp.CellSize = desc(roadsTravelTimeRaster).MeanCellWidth
    
    print ('1.'+time.ctime()+ ' Extracting urban cores ' + decade)
    neighborDensClass = houseDensWorkspace + '/nghDnsCls' + decade     
    urbanCores = houseDensWorkspace + '/cores' + decade    
    gp.ExtractByAttributes_sa(neighborDensClass, '"VALUE" = 1 OR "VALUE" = 2', urbanCores)
    
    print ('2. Reclassifying urban cores ' + decade)
    urbanCoresReclass = houseDensWorkspace + '/coresrcls' + decade    
    gp.Reclassify_sa(urbanCores, 'VALUE', '0 2 1', urbanCoresReclass)
    
    print ('3. Grouping urban cores ' + decade)
    urbanCoresGroup = houseDensWorkspace + '/coresgrp' + decade    
    gp.RegionGroup_sa(urbanCoresReclass, urbanCoresGroup, 'EIGHT', 'WITHIN', 'ADD_LINK', '')
    
    print ('4. Applying urban core size threshold ' + decade)
    urbanPatch = houseDensWorkspace + '/urbnpatch' + decade    
    reclassRange = '0 '+str(urbanPatchSize)+ ' NoData;' +str(urbanPatchSize) + ' 9999999 1;'    
    gp.Reclassify_sa(urbanCoresGroup, 'Count', reclassRange, urbanPatch, 'DATA')
    
    print ('5. Calculating cost distance ' + decade)
    urbanCstDst = houseDensWorkspace + '/urbnCsDs' + decade    
    gp.CostDistance_sa(urbanPatch, roadsTravelTimeRaster, urbanCstDst, "", "")
    
    print ('6. Applying time factor thresholds ' + decade)
    timeClassUrbnCenter = houseDensWorkspace + '/tiClsUrbn' + decade    
    gp.Reclassify_sa(urbanCstDst, 'VALUE', '0 5 1; 5 10 2; 10 20 3; 20 30 4; 30 45 5; 45 9999 6;', timeClassUrbnCenter, "DATA")
    
    print ('7. Euclidean allocation ' + decade)
    urbanCstDstAlloc = houseDensWorkspace + '/urbnCsDsA' + decade    
    gp.EucAllocation_sa(timeClassUrbnCenter, urbanCstDstAlloc, "", "", "100", "Value", "", "")

    if delTemp == 'yes':
        try:
            print ('8. deleting temp layers')
            gp.delete(urbanCores)
            gp.delete(urbanCoresReclass)
            gp.delete(urbanCoresGroup)
            gp.delete(urbanPatch)
        except:
            print (' -trouble deleting layers')
            print ('9. Finished ' + decade)
    else:
        print ('9. Finished ' + decade)
    

#----------------------------------------------------------------------------------------
# Theobald's default function for calculating growth trends (at STATE level)
def averageChangeHousingUnits(gp, developMaskRaster, decade1, decade2, counties, delTemp):
    neighborDensClass1 = houseDensWorkspace + '/nghDnsCls' + decade1
    neighborDensClass2 = houseDensWorkspace + '/nghDnsCls' + decade2    
    blockHousingDensity1 = houseDensWorkspace + '/hd_' + decade1
    blockHousingDensity2 = houseDensWorkspace + '/hd_' + decade2
    
    desc = gp.Describe
    gp.Mask = developMaskRaster
    gp.Extent = desc(developMaskRaster).Extent
    gp.CellSize = desc(developMaskRaster).MeanCellWidth

    print ('1. '+time.ctime()+ ' Growth class ' + decade1+ ' and ' +decade2)
    urbanCstDstAlloc1 = houseDensWorkspace + '/urbnCsDsA' + decade1
    growthClass1 = houseDensWorkspace + '/grwthcls' + decade1    
    mapAlgebra = "(" + neighborDensClass1+ " * 10 ) +" +urbanCstDstAlloc1
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthClass1)
    
    urbanCstDstAlloc2 = houseDensWorkspace + '/urbnCsDsA' + decade2
    growthClass2 = houseDensWorkspace + '/grwthcls' + decade2    
    mapAlgebra = "(" + neighborDensClass2+ " * 10 ) +" +urbanCstDstAlloc2
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthClass2)
    
    print ('2. Calculate growth rate between ' +decade1+ ' and ' +decade2)
    growRate = houseDensWorkspace + '/gr' + decade1 + decade2
    mapAlgebra3 = "(" +blockHousingDensity1+" - "+blockHousingDensity2+") / "+blockHousingDensity2
    gp.SingleOutputMapAlgebra_sa(mapAlgebra3, growRate)
    
    print ('3. Calculate growth units between ' +decade1+ ' and ' +decade2)
    growUnits = houseDensWorkspace + '/gu_' + decade1 + decade2    
    mapAlgebra4 = "(" +blockHousingDensity1+" - "+blockHousingDensity2+")"
    gp.SingleOutputMapAlgebra_sa(mapAlgebra4, growUnits)
    
    print ('4. Create zonal stats grid between ' +decade1+ ' and ' +decade2)
    avgGrowthCls = houseDensWorkspace + '/avgGrwCls' +decade1    
    gp.ZonalStatistics_sa (growthClass2, "VALUE", growUnits, avgGrowthCls, "MEAN", "DATA")
    
#----------------------------------------------------------------------------------------
# Dan's adjusted mechanism for calculating trends at COUNTY level
def averageChangeHousingUnits2(gp, developMaskRaster, decade1, decade2, counties, delTemp):
    neighborDensClass1 = houseDensWorkspace + '/nghDnsCls' + decade1
    neighborDensClass2 = houseDensWorkspace + '/nghDnsCls' + decade2    
    blockHousingDensity1 = houseDensWorkspace + '/hd_' + decade1
    blockHousingDensity2 = houseDensWorkspace + '/hd_' + decade2
    
    desc = gp.Describe
    gp.Mask = developMaskRaster
    gp.Extent = desc(developMaskRaster).Extent
    gp.CellSize = desc(developMaskRaster).MeanCellWidth

    print ('1. '+time.ctime()+ ' Growth class ' + decade1+ ' and ' +decade2)
    urbanCstDstAlloc1 = houseDensWorkspace + '/urbnCsDsA' + decade1
    growthClass1 = houseDensWorkspace + '/grwthcls' + decade1    
    mapAlgebra = counties+ "+ (" +neighborDensClass1+ " * 10 ) +" +urbanCstDstAlloc1
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthClass1)
    
    urbanCstDstAlloc2 = houseDensWorkspace + '/urbnCsDsA' + decade2
    growthClass2 = houseDensWorkspace + '/grwthcls' + decade2    
    mapAlgebra = counties+ "+ (" +neighborDensClass2+ " * 10 ) +" +urbanCstDstAlloc2
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthClass2)

    print ('2. Sum ' +decade1+ ' houses within growth class ' +decade1)
    houses1 = houseDensWorkspace + '/houses' +decade1    
    gp.ZonalStatistics_sa (growthClass2, "VALUE", blockHousingDensity1, houses1, "SUM", "DATA")

    print ('3. Sum ' +decade2+ ' houses within growth class ' +decade1)
    houses2 = houseDensWorkspace + '/houses' +decade2    
    gp.ZonalStatistics_sa (growthClass2, "VALUE", blockHousingDensity2, houses2, "SUM", "DATA")

    print ('4. Subtract ' +decade2+ ' from ' +decade1+ ' houses to calculate number of new houses in each class')    
    newHouses = houseDensWorkspace + '/newhs' + decade1 + decade2    
    mapAlgebra4 = "(" +houses1+" - "+houses2+")"
    gp.SingleOutputMapAlgebra_sa(mapAlgebra4, newHouses)   
    
    print ('5. Calculate zonal stats to get state total number houses in ' +decade1)
    house1 = houseDensWorkspace + '/house' +decade1    
    gp.ZonalStatistics_sa (counties, "VALUE", blockHousingDensity1, house1, "SUM", "DATA")

    print ('6. Calculate zonal stats to get state total number houses in ' +decade2)
    house2 = houseDensWorkspace + '/house' +decade2    
    gp.ZonalStatistics_sa (counties, "VALUE", blockHousingDensity2, house2, "SUM", "DATA")    

    print ('7. Subtract ' +decade2+ ' from ' +decade1+ ' houses to calculate number of new houses in state')    
    stateNewHouses = houseDensWorkspace + '/sths' + decade1 + decade2    
    mapAlgebra4 = "(" +house1+" - "+house2+")"
    gp.SingleOutputMapAlgebra_sa(mapAlgebra4, stateNewHouses)    
    
    print ('8. Divide step 4 by step 5 to get fraction of new houses in each class')    
    avgGrowthPerCls = houseDensWorkspace + '/avgPerCls' +decade1
    mapAlgebra3 = newHouses+ " / "+stateNewHouses
    gp.SingleOutputMapAlgebra_sa(mapAlgebra3, avgGrowthPerCls)

    print ('9. Create Raster of Counts of each growth class')
    clsCount = houseDensWorkspace + '/clscount' +decade1
    gp.Lookup_sa(growthClass1, "Count", clsCount)
       
    print ('10. Divide % of houses in each class by area of each class to get average density increase')
    avgGrowthCls = houseDensWorkspace + '/avgGrwCls' +decade1
    mapAlgebra5 = avgGrowthPerCls+ " / "+clsCount
    gp.SingleOutputMapAlgebra_sa(mapAlgebra5, avgGrowthCls)
      
#----------------------------------------------------------------------------------------
# Dan's adjusted mechanism for calculating trends at STATE level
def averageChangeHousingUnits3(gp, developMaskRaster, decade1, decade2, state, delTemp):
    neighborDensClass1 = houseDensWorkspace + '/nghDnsCls' + decade1
    neighborDensClass2 = houseDensWorkspace + '/nghDnsCls' + decade2    
    blockHousingDensity1 = houseDensWorkspace + '/hd_' + decade1
    blockHousingDensity2 = houseDensWorkspace + '/hd_' + decade2
    
    desc = gp.Describe
    gp.Mask = developMaskRaster
    gp.Extent = desc(developMaskRaster).Extent
    gp.CellSize = desc(developMaskRaster).MeanCellWidth

    print ('1. '+time.ctime()+ ' Growth class ' + decade1+ ' and ' +decade2)
    urbanCstDstAlloc1 = houseDensWorkspace + '/urbnCsDsA' + decade1
    growthClass1 = houseDensWorkspace + '/grwthcls' + decade1
    mapAlgebra = "(" + neighborDensClass1+ " * 10 ) +" +urbanCstDstAlloc1
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthClass1)
    
    urbanCstDstAlloc2 = houseDensWorkspace + '/urbnCsDsA' + decade2
    growthClass2 = houseDensWorkspace + '/grwthcls' + decade2
    mapAlgebra = "(" + neighborDensClass2+ " * 10 ) +" +urbanCstDstAlloc2
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthClass2)

    print ('2. Sum ' +decade1+ ' houses within growth class ' +decade1)
    houses1 = houseDensWorkspace + '/houses' +decade1    
    gp.ZonalStatistics_sa (growthClass2, "VALUE", blockHousingDensity1, houses1, "SUM", "DATA")

    print ('3. Sum ' +decade2+ ' houses within growth class ' +decade1)
    houses2 = houseDensWorkspace + '/houses' +decade2    
    gp.ZonalStatistics_sa (growthClass2, "VALUE", blockHousingDensity2, houses2, "SUM", "DATA")

    print ('4. Subtract ' +decade2+ ' from ' +decade1+ ' houses to calculate number of new houses in each class')    
    newHouses = houseDensWorkspace + '/newhs' + decade1 + decade2    
    mapAlgebra4 = "(" +houses1+" - "+houses2+")"
    gp.SingleOutputMapAlgebra_sa(mapAlgebra4, newHouses)   
    
    print ('5. Calculate zonal stats to get state total number houses in ' +decade1)
    house1 = houseDensWorkspace + '/house' +decade1    
    gp.ZonalStatistics_sa (state, "VALUE", blockHousingDensity1, house1, "SUM", "DATA")

    print ('6. Calculate zonal stats to get state total number houses in ' +decade2)
    house2 = houseDensWorkspace + '/house' +decade2    
    gp.ZonalStatistics_sa (state, "VALUE", blockHousingDensity2, house2, "SUM", "DATA")    

    print ('7. Subtract ' +decade2+ ' from ' +decade1+ ' houses to calculate number of new houses in state')    
    stateNewHouses = houseDensWorkspace + '/sths' + decade1 + decade2    
    mapAlgebra4 = "(" +house1+" - "+house2+")"
    gp.SingleOutputMapAlgebra_sa(mapAlgebra4, stateNewHouses)    
    
    print ('8. Divide step 4 by step 5 to get fraction of new houses in each class')    
    avgGrowthPerCls = houseDensWorkspace + '/avgPerCls' +decade1
    mapAlgebra3 = newHouses+ " / "+stateNewHouses
    gp.SingleOutputMapAlgebra_sa(mapAlgebra3, avgGrowthPerCls)

    print ('9. Create Raster of Counts of each growth class')
    clsCount = houseDensWorkspace + '/clscount' +decade1
    gp.Lookup_sa(growthClass1, "Count", clsCount)
       
    print ('10. Divide % of houses in each class by area of each class to get average density increase')
    avgGrowthCls = houseDensWorkspace + '/avgGrwCls' +decade1
    mapAlgebra5 = avgGrowthPerCls+ " / "+clsCount
    gp.SingleOutputMapAlgebra_sa(mapAlgebra5, avgGrowthCls)    
    
#----------------------------------------------------------------------------------------
def createPopGrids(gp, developMaskRaster, projPopWorkspace, decade, decade1, decade2, slopeTweak, delTemp):
    decade = str(decade)
    popDecade = projPopWorkspace + '/pop' + decade
    popDecade1 = projPopWorkspace + '/pop' + decade1
    popDecade2 = projPopWorkspace + '/pop' + decade2    
    blockHousingDensity = houseDensWorkspace + '/hd_' + decade
    blockHousingDensity1 = houseDensWorkspace + '/hd_' + decade1
    blockPopulationDensity = projPopWorkspace + '/bPopDens' + decade
    urbanCstDst = houseDensWorkspace + '/urbnCsDs' + decade1

    desc = gp.Describe
    gp.Mask = developMaskRaster
    gp.Extent = desc(developMaskRaster).Extent
    gp.CellSize = desc(developMaskRaster).MeanCellWidth
    
    print ('1. '+time.ctime()+ ' Calculate new growth ' + decade1)
    newPop = projPopWorkspace + '/popchange' + decade    
    mapAlgebra = "max (" + popDecade+ " - " +popDecade1+ ")"  #This might need to be decade - decade 1 (2010 - 2000)
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, newPop)    

    print ('2. Adjust growth ' + decade1)
    neighborDensClass = houseDensWorkspace + '/nghDnsCls' + decade1
    growAvg = houseDensWorkspace + '/avgGrwCls' + decade1    
    growAvg2 = projPopWorkspace + '/growAvg2_' + decade
    mapAlgebra = "con (" +neighborDensClass+ " < 3,(0.5 * " +growAvg+ "), con (" +neighborDensClass+ " == 3,( 0.8 * " +growAvg+ "), "+growAvg+ "))" #Uncomment this for DT's tweaks; removed int statements    
#    mapAlgebra = "con (" +neighborDensClass+ " < 3, (1 * " +growAvg+ "), con (" +neighborDensClass+ " == 3, ( 1 * " +growAvg+ "), "+growAvg+ "))" 
    gp.SingleOutputMapAlgebra_sa (mapAlgebra,growAvg2)

    print ('3. Calculate tweaks on empirical growth rate as function of travel time ')
    growthTweak = projPopWorkspace + '/growtweak' + decade    
    mapAlgebra = "con (" +urbanCstDst+ " < 5.0, " +allocWeightLt5+ ", con ( " +urbanCstDst+ " < 10.0, " +allocWeight5_10+ ", con ( " +urbanCstDst+ " < 20.0, " +allocWeight10_20+ ", con ( " +urbanCstDst+ " < 30.0, " +allocWeight20_30+ ", con ( " +urbanCstDst+ " < 45.0, " +allocWeight30_45+ ", " +allocWeightGt45+ ") ) ) ) )"
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growthTweak)

    print ('4. Multiply avg # of housing units/person by change in population to calculate # of new houses')
    newUnits = projPopWorkspace + '/newunits' + decade
    mapAlgebra = "int((" +householdSizeInverse+ " * " +unitsPerPerson+ ") * " +newPop+ ")"
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, newUnits)

    print ('5. Multiply householdSizeInverse (usually = 1; step 5) by travel time tweak (step 3) and density tweak (step 2) ')   
    growWeights = projPopWorkspace + '/growghts' + decade
#    mapAlgebra = "( " +growAvg2+ " * ( " +growthTweak+ " / 100.0) * " +householdSizeInverse+ ")" #Uncomment to remove slope tweak
    mapAlgebra = "( " +growAvg2+ " * ( " +growthTweak+ " / 100.0) * ( " +slopeTweak+ " / 100.0)* " +householdSizeInverse+ ")"    
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, growWeights)  
    
    print ('6. Calculate sum of growWeights in population projection unit (county, sub-county, etc) ')   
    sumGrowWeights = projPopWorkspace + '/growghts2' + decade
    gp.ZonalStatistics_sa (populationProjectionPolygon, "VALUE", growWeights, sumGrowWeights, "SUM", "DATA")

    print ('7. Calculate relative grow weights for each pixel in population projection unit (county, sub-county, etc)')             
    cWeights = projPopWorkspace + '/cweights' + decade
    mapAlgebra = growWeights+ " / " +sumGrowWeights
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, cWeights)

    print ('8. Calculate average number of units per population projection unit ')
    newUnits2 = projPopWorkspace + '/newunits2' + decade
    gp.ZonalStatistics_sa (populationProjectionPolygon, "VALUE", newUnits, newUnits2, "MEAN", "DATA")    

    print ('9. Calculate new housing units per pixel')             
    newUnits3 = projPopWorkspace + '/newunits3' + decade
    mapAlgebra = newUnits2+ " * " +cWeights 
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, newUnits3)

    print ('10. Add new housing units to previous decade to get new housing density grid')
    blockHousingDensity1 = houseDensWorkspace + '/hd_' + decade1
    newBlockHousingDensity = houseDensWorkspace + '/hd_' + decade
    mapAlgebra = "con ( isnull( " +newUnits3+ "), " +blockHousingDensity1+ ", " +blockHousingDensity1+ " + " +newUnits3+ " )"
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, newBlockHousingDensity)

    print ('11. Calculate new population per pixel')             
    newPopUnits = projPopWorkspace + '/newpop' + decade
    mapAlgebra = newPop+ " * " +cWeights 
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, newPopUnits)    

    print ('13. Add new population to previous decade to get new population density grid')
    blockPopDensity1 = houseDensWorkspace + '/pd_' + decade1
    newBlockPopDensity = houseDensWorkspace + '/pd_' + decade
    mapAlgebra = "con ( isnull( " +newPopUnits+ "), " +blockPopDensity1+ ", " +blockPopDensity1+ " + " +newPopUnits+ " )"
    gp.SingleOutputMapAlgebra_sa (mapAlgebra, newBlockPopDensity)
    


import sys, string, os, time
from gen_checkArcGisVersion import *
from gen_reportErrors import *
##from gen_logFile import *
gp = checkArcGIS()
import gen_checkExtensions

try:
# Arguments ------------------------------#####
##    developMaskRaster = sys.argv[1]
##    houseDensWorkspace = sys.argv[2]
##    projPopWorkspace = sys.argv[3]
##    roadsTravelTimeRaster = sys.argv[4]
##    coFipsRaster = sys.argv[5]
##    unitsPerPopRatioAdjust = sys.argv[6]
##    householdSizeInverse = 1.0   
##    # housing density thresholds    
##    thresholdUrban = 4118
##    thresholdSuburban = 1454
##    thresholdExurban = 62
##    thresholdRural = 1   
##    # weights for tweaking allocation surface
##    allocWeightLt5 = 90
##    allocWeight5_10 = 95
##    allocWeight10_20 = 85
##    allocWeight20_30 = 90
##    allocWeight30_45 = 95
##    allocWeightGt45 = 100

# data inputs
    developMaskRaster = "G:/Working/Analysis/Growth/developmentMask.gdb/developmask_lfpsosindmil"
    houseDensWorkspace = "G:/Working/Analysis/Growth/houseDensityWorkspace"
    projPopWorkspace = "G:/Working/Analysis/Growth/projPopWorkspace"
    roadsTravelTimeRaster = "G:/Working/Analysis/Growth/growthInputs.gdb/road_min_per_pixel2"
#    unitsPerPerson = "G:/Working/Analysis/Growth/growthInputs.gdb/tracts_2000_unitsperperson"
    unitsPerPerson = "G:/Working/Analysis/Growth/growthInputs.gdb/unitsperperson_county"    
    populationProjectionPolygon = projPopWorkspace + '/pop_project'
    slope = "G:/Working/Analysis/Growth/developmentMask.gdb/slope_percent_100b"
    counties = "G:/Working/Analysis/Growth/growthInputs.gdb/counties2"
    state = "G:/Working/Analysis/Growth/growthInputs.gdb/state"    
    delTemp = 'yes'
# housing density thresholds    
    thresholdUrban = 10
    thresholdSuburban = 1.47
    thresholdExurban = 0.06
    thresholdRural = 0
# urban patch size, assuming 500m cells
#    urbanPatchSize = 100 #set this to 100 100m cells; If 500m cells, then set it to 4. Urban patch > 100 ha w/ 500m cells
    urbanPatchSize = 500

# travel time factor
##    travelTimeFactor = 100000 #Not needed if cost distance grid isn't converted to integer
# household size inverse  
    householdSizeInverse = str(1.0)

# weights for tweaking allocation surface
    allocWeightLt5 = str(90)
    allocWeight5_10 = str(95)
    allocWeight10_20 = str(85)
    allocWeight20_30 = str(90)
    allocWeight30_45 = str(95)
    allocWeightGt45 = str(100)

# weights for tweaking allocation surface
##    allocWeightLt5 = str(100)
##    allocWeight5_10 = str(100)
##    allocWeight10_20 = str(100)
##    allocWeight20_30 = str(100)
##    allocWeight30_45 = str(100)
##    allocWeightGt45 = str(100)    

# weights for tweaking allocation surface
##    allocWeightLt5 = str(75)
##    allocWeight5_10 = str(75)
##    allocWeight10_20 = str(85)
##    allocWeight20_30 = str(90)
##    allocWeight30_45 = str(95)
##    allocWeightGt45 = str(100) 
    
    
# Utility stuff ------------------------------#####
    gen_checkExtensions.checkSpatialAnalyst(gp)
    gp.OverwriteOutput = 1                                                  
    totalSteps = '4'
    toolName = 'SergomCustom'
##    inParameters = '%s ' % (clipFeature)
##    logFile = createLogFile(workspace, toolName, inParameters)    
    gp.AddMessage('')
    gp.AddMessage('SERGoM Arizona ----------------------------------------')
    gp.AddMessage('RUNNING: SERGoM growth model') 
    gp.AddMessage('')
# Spatial analyst environment
##    desc = gp.Describe
##    gp.Extent = desc(developMask).Extent

# Call functions ------------------------------#####
    try:
# 1. Calculate stuff for 1990 base data first?
        print ('START TIME: '+time.ctime())
        print (' Prestep 1: Calculating neighborhood density for 1990')           
        neighDensityDecade1 = neighborhoodDensity(gp, houseDensWorkspace, '1990', thresholdUrban, thresholdSuburban, thresholdExurban, delTemp)

        print (' Prestep 2: Calculating neighborhood density for 1990')
        distanceFromUrbanClasses(gp,houseDensWorkspace, '1990', roadsTravelTimeRaster, urbanPatchSize, delTemp)

        print (' Prestep 3: Calculate slope weights')
        slopeTweakInt = houseDensWorkspace + '/slptweaki' 
        slopeTweak = houseDensWorkspace + '/slptweak' 
        gp.Reclassify_sa(slope, 'VALUE', '0 2 100; 2 5 90; 5 10 60; 10 15 40; 15 20 30; 20 25 10; 25 100000 0', slopeTweakInt)
        gp.Float_sa(slopeTweakInt, slopeTweak)
        gp.delete(slopeTweakInt)
        print (' ')

        
        for x in [2010, 2020, 2030, 2040, 2050]: 
            decade = str(x)
            decade1 = str(x-10)
            decade2 = str(x-20)

# 1. Calculate neighborhood density
            print (' Step 1/'+totalSteps+') Calculating neighborhood density')
            neighborhoodDensity(gp, houseDensWorkspace, decade1, thresholdUrban, thresholdSuburban, thresholdExurban, delTemp)
            print (' ')

# 2. Calculate distance from urban classes
            print (' Step 2/'+totalSteps+') Calculating distance from urban classes')
            distanceFromUrbanClasses(gp,houseDensWorkspace, decade1, roadsTravelTimeRaster, urbanPatchSize, delTemp)
            print (' ')
            
# 3. Calculate change in housing units        
            print (' Step 3/'+totalSteps+') Calculating change in housing units')
            averageChangeHousingUnits3(gp, developMaskRaster, decade1, decade2, state, delTemp)
            print (' ')
            
# 4. Create new population grid based on previous time step's growth rate        
            print (' Step 4/'+totalSteps+') Creating new population grid')
            createPopGrids (gp, developMaskRaster, projPopWorkspace, decade, decade1, decade2, slopeTweak, delTemp)
            print (decade+ ' DONE')
            print (' ')
    except:
        addErrorMessages(gp)
##        closeLogFile(logFile)
        del gp
    print ('END TIME: '+time.ctime())

except:
    addErrorMessages(gp)
##    closeLogFile(logFile)
    del gp
