#Script to open Root files saved in the Plotter stage of TauFW
#It takes the TCanvas object and extract the corresponding histograms in the stack + the data hist
#It returns a Root file with TH1D, that can be used as an input to the plot_mvis_uncorr_corr.py script to produce paper-quality plots
#Author: Paola Mastrapasqua
#Date  : September 2025
   
import ROOT

# Open the ROOT file
file_in = ROOT.TFile.Open("plots/2022_postEE/etau/mvis_et-tightVsele-2022_postEE.root")

# Check if the file is successfully opened
if not file_in or file_in.IsZombie():
    print("Error: Unable to open ROOT file")
    exit()

# Get the TCanvas saved in the ROOT file
canvas = file_in.Get("canvas")

# Check if the canvas is found
if not canvas:
    print("Error: Canvas not found in the ROOT file")
    file_in.Close()
    exit()

file_out = ROOT.TFile("22postEE_et_uncorrected.root", "RECREATE")
# Get the list of primitives (histograms, functions, etc.) drawn on the canvas
primitives = canvas.GetListOfPrimitives()

# Loop through the list to access each histogram
for obj in primitives:
    #print(obj.GetName())
    subprims = obj.GetListOfPrimitives()
    for subprim in subprims:
        #print(subprim.GetName())
        if subprim.GetName() == "stack_mvis":
           histograms = subprim.GetHists()
           for hist in histograms:
               if hist.GetName().startswith("mvis"):  
                  print(">>>Histogram Name:", hist.GetName())
                  #print("Integral: ", hist.Integral())
                  #file_out.cd()
                  hist.Write()
               
        if isinstance(subprim, ROOT.TH1):
           if subprim.GetName().startswith("mvis"):   
              print("Histogram Name:", subprim.GetName())
              #print("Integral: ", subprim.Integral())
              #file_out.cd()
              subprim.Write()

file_in.Close()
file_out.Close()
