#!/bin/bash
filename=PlotShapes.C
#####VARIABLE DECLARATION

###SETTING WPs
#declare -a arr=("VVLoose" "VLoose" "Loose" "Medium" "Tight" "VTight" "VVTight")
declare -a arr=("VLoose")
part="VVLoose"

###SETTING ETA
defaulteta="Lt1p46"
#SET YOUR ETA RANGE BELOW!
neweta="Lt2p300"

###SETTING ERA
defaultera="UL2017"
#SET YOUR ERA BELOW!
newera="UL2018"


###EXECUTE
sed -i "0,/$defaulteta/s/$defaulteta/$neweta/" $filename 
sed -i "0,/$defaultera/s/$defaultera/$newera/" $filename 


## now loop through the above array
for i in "${arr[@]}"
do
      
  sed -i "s/$part/$i/" $filename
  
  root -b -q PlotShapes.C

  search="bool posfit = true,"
  replace="bool posfit = false,"

  sed -i "s/$search/$replace/" $filename

  root -b -q PlotShapes.C


  searchA="bool passProbe = true,"
  replaceA="bool passProbe = false,"

  sed -i "s/$searchA/$replaceA/" $filename

  root -b -q PlotShapes.C


  searchB="bool posfit = false,"
  replaceB="bool posfit = true,"

  sed -i "s/$searchB/$replaceB/" $filename

  root -b -q PlotShapes.C

  searchC="bool passProbe = false,"
  replaceC="bool passProbe = true,"


  sed -i "s/$searchC/$replaceC/" $filename

  sed -i "s/$i/$part/" $filename
done

###RESET EVERYTHING TO DEFAULT VALUES
sed -i "0,/$neweta/{s/$neweta/$defaulteta/}" $filename 
sed -i "0,/$newera/{s/$newera/$defaultera/}" $filename 
