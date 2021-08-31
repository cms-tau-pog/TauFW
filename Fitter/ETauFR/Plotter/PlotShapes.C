///----------------------Version 1.0-------------------------//
///Plotting Macro for E -> Tau Fake Rates study
///Author: Yiwen Wen
///DESY
///-----------------------------------------------------------//
#include <iostream>
#include <vector>
#include <map>
#include <iomanip>
#include "boost/lexical_cast.hpp"
#include "boost/algorithm/string.hpp"
#include "boost/format.hpp"
#include "boost/program_options.hpp"
#include "boost/range/algorithm.hpp"
#include "boost/range/algorithm_ext.hpp"
#include "./Plotting.h"
#include "./Plotting_Style.h"
#include "./HttStylesNew.cc"
#include "TFile.h"
#include "TH1.h"
#include "TROOT.h"
#include "TColor.h"
#include "TEfficiency.h"
#include "TMath.h"
void PlotShapes(
		TString varName= "m_vis",
		TString xtitle = "m_{vis} [GeV]",
		TString ytitle = "dN/dm_{vis}[1/GeV]",
		//SET YOUR ERA HERE !!!!!!
		//TString era = "UL2016_preVFP",
		//TString era = "UL2016_postVFP",
		TString era = "UL2017",
		//SET YOUR ETA RANGE HERE !!!!
		TString eta = "Lt1p46",
		//TString eta = "Lt2p300",
		TString wp = "VVLoose",
		float xmin = 60,
		float xmax = 120,
		int numberofbins = 12,
		//CHOOSE YOUR PRE OR POST FIT. CHOOSE FAIL OR PASS REGION
		bool posfit = true,
		bool passProbe = true,
		bool logY = false,
		bool legLeft = false
		)
{
  //SetStyle();
  //SET YOUR LUMI HERE AND IN THE CANVAS BELOW !!!!!!
  //float lumi= 59970;
  float lumi;
  if(era == "UL2017") lumi = 41860;//UL17
  else if(era == "UL2018") lumi = 59800;//UL18
  else if(era == "UL2016_preVFP") lumi = 19500;//UL16_preVFP
  else if(era == "UL2016_postVFP") lumi = 16800;//UL16_postVFP
  else lumi= 59970;

  //float lumi = 59800;//UL18
  //float lumi = 19500;//UL16_preVFP
  //float lumi = 16800;//UL16_postVFP

  //Deal with bins and binning
  float xMin = xmin;
  float xMax = xmax;
  int nBins = numberofbins;
  float bins[100];
  float binWidth = (xMax-xMin)/float(nBins);
  for (int iB=0; iB<=nBins; ++iB)
    bins[iB] = xMin + float(iB)*binWidth;
    
  TString suffix;

  if(posfit)
    suffix = "_postfit";
  else
    suffix = "_prefit";
    
  TString suffixPassOrFail;
    
  if(passProbe)
    suffixPassOrFail = "_pass";
  else
    suffixPassOrFail = "_fail";
    

  cout << "Accessing the File" <<endl;
  
  TFile * file = new TFile("../PostFitShape/"+era+"/ETauFR"+wp+eta+"_PostFitShape.root");
  cout << "File opened!" <<endl;
  TH1D * data_obs = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/data_obs");
  cout << "data_obs found!" <<endl;
  //TH1D * ZEE = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZEE"); //LOR COMM
  TH1D * ZEE = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZL"); //LOR COMM
  TH1D * ZJ = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZJ");
  //if(wp !="VVLoose" && eta!="Gt1p558")
  //TH1D * ZTT_el = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZTT_el");    //LOR COMM
  //TH1D * ZTT_et = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZTT_et"); //LOR COMM
  TH1D * ZTT_et = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZTT"); //LOR COMM
  cout << "All Zxx histos found" <<endl;
  //TH1D * TT = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/TT"); //LOR COMM
  TH1D * TT = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/TTT"); //LOR COMM
  TH1D * VV = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/VV");
  TH1D * W = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/W");
  TH1D * QCD = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/QCD");
  //if(eta =="0p8to1p2" && !passProbe) TH1D * W = (TH1D*)VV->Clone("W");//brute force no W in this region
  cout << "All the TH1D are loaded" <<endl;
  //TH1D * dummy = (TH1D*)ZEE->Clone("dummy"); //LOR COMM
  if(ZTT_et==NULL){cout << "ZTT is NULL!!!!" <<endl;}
  TH1D * dummy = (TH1D*)ZTT_et->Clone("dummy");
  cout << "dummy TH1D is created" <<endl;  
  //TH1D Added by LOR
  //TH1D * ZTT = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/ZTT");
  //TH1D * TTT = (TH1D*)file->Get("/"+wp+suffixPassOrFail+suffix+"/TTT");
  


  float errLumi = 0.062;
  float errQCD = 0.3;
  float errDY=0.03;
  float errVV = 0.1;
  float errW = 0.2;
  //float errTT = 0.1; //LOR COMM
  float errTT = 0.1;
  //float errTTT = 0.1;
  float errTauID = 0.03;
  float errEleID = 0.05;
  cout << "Start Loop on Bins" <<endl;  
  for (int iB=1; iB<=nBins; ++iB)
    {
      float eQCD = 0;
      if(QCD)errQCD*(QCD->GetBinContent(iB));
      float eVV = errVV*(VV->GetBinContent(iB));
      float eDYEE = errDY*2*(ZEE->GetBinContent(iB));
      float eDYZJ = errDY*(ZJ->GetBinContent(iB));
      //float eDYZTT_el = errDY*ZTT_el->GetBinContent(iB);
      float eDYZTT_et = errDY*(ZTT_et->GetBinContent(iB));

      float eW;
      //if(!passProbe && eta=="0p8to1p2") eW = 0;
      if(W!=NULL){eW = errW*(W->GetBinContent(iB));}

      float eTT = errTT*(TT->GetBinContent(iB));
      float err2 = eQCD*eQCD + eVV*eVV + eW*eW + eTT*eTT+eDYEE*eDYEE+eDYZJ*eDYZJ+eDYZTT_et*eDYZTT_et;
      float errTot = TMath::Sqrt(err2);
      dummy->SetBinError(iB,errTot);
    }
  float numberZEE = ZEE->GetSumOfWeights();
    
  if(W!=NULL){W->Add(W,QCD);}
  TT->Add(TT,W);
  VV->Add(VV,TT);
  ZTT_et->Add(ZTT_et,VV);
  /* LOR COMM
  if(ZTT_el!=NULL)
    {
      ZTT_el->Add(ZTT_el,ZTT_et);
      ZJ->Add(ZJ,ZTT_el);
    }
  else
    ZJ->Add(ZJ,ZTT_et);
  */  
  ZJ->Add(ZJ,ZTT_et);//LOR COMM
  ZEE->Add(ZEE,ZJ);
    
  float totData = data_obs->GetSumOfWeights();
  float totMC = ZEE->GetSumOfWeights();
  
  TH1D * bkgdErr = (TH1D*)ZEE->Clone("bkgdErr");
  bkgdErr->SetFillStyle(3013);
  bkgdErr->SetFillColor(1);
  bkgdErr->SetMarkerStyle(21);
  bkgdErr->SetMarkerSize(0);
    
  for (int iB=1; iB<=nBins; ++iB)
    {  
      if(W!=NULL) W->SetBinError(iB,0);
      if(QCD)QCD->SetBinError(iB,0);
      VV->SetBinError(iB,0);
      TT->SetBinError(iB,0);
      ZTT_et->SetBinError(iB,0);

      ZJ->SetBinError(iB,0);
      ZEE->SetBinError(iB,0);
      float eStat =  bkgdErr->GetBinError(iB);
      float X = bkgdErr->GetBinContent(iB);
      float eLumi = errLumi * X;
      float eBkg = dummy->GetBinError(iB);
      float Err=0; 
      if(posfit)
        {
	  Err = TMath::Sqrt(eStat*eStat);
        }
      else
        {
	  Err = TMath::Sqrt(eLumi*eLumi+eBkg*eBkg+errEleID*errEleID+errTauID*errTauID+eStat*eStat);
	  //float Err = TMath::Sqrt(eStat*eStat);
        }
      //float normalErr = TMath::Sqrt(eLumi*eLumi+eBkg*eBkg+errEleID*errEleID);
      //errZEE = normalErr+errZEE;//for calcluating Fake rate error
      bkgdErr->SetBinError(iB,Err);
    }
    
  //Colors
  Int_t colorZEE = TColor::GetColor("#ffcc66");
  Int_t colorZJ = TColor::GetColor("#4496C8");
  Int_t colorTT = TColor::GetColor("#9999CC");
  Int_t colorVV = TColor::GetColor("#6F2D35");
  Int_t colorW = TColor::GetColor("#DE5A6A");
  Int_t colorQCD = TColor::GetColor("#FFCCFF");

  cout << "Init Data and Hist" <<endl;
  InitData(data_obs);
  if(QCD)InitHist(QCD,TColor::GetColor("#FFCCFF"));
  InitHist(ZEE,TColor::GetColor("#DE5A6A"));
  InitHist(TT,TColor::GetColor("#9999CC"));
  InitHist(VV,TColor::GetColor("#6F2D35"));
  InitHist(ZJ,TColor::GetColor("#FFCC66"));
  if(W!=NULL) {InitHist(W,TColor::GetColor("#4496C8"));}
  data_obs->SetTitle("");
  data_obs->SetStats(0);
  data_obs->GetXaxis()->SetTitle(xtitle);
  data_obs->GetYaxis()->SetTitle(ytitle);
  data_obs->GetYaxis()->SetTitleOffset(1.5);
  data_obs->GetYaxis()->SetTitleSize(0.06);
  data_obs->GetXaxis()->SetRangeUser(xmin,xmax);
  float ymax = data_obs->GetMaximum();
  if (logY)
    data_obs->GetYaxis()->SetRangeUser(0.5,2*ymax);
  else
    data_obs->GetYaxis()->SetRangeUser(0,1.3*ymax);
  data_obs->SetMarkerSize(1.5);
  data_obs->GetXaxis()->SetLabelSize(0);
  data_obs->GetYaxis()->SetLabelSize(0.06);
  
  cout << "All Hist are loaded. Init TCanvas" <<endl;
  TCanvas * canv1 = new TCanvas("canv1", "", 1000, 800);
  
  TPad *upper = new TPad("upper", "pad",0,0.31,1,1);
  upper->Draw();
  upper->cd();
  upper->SetFillColor(0);
  upper->SetBorderMode(0);
  upper->SetBorderSize(10);
  upper->SetTickx(1);
  upper->SetTicky(1);
  upper->SetLeftMargin(0.17);
  upper->SetRightMargin(0.05);
  upper->SetBottomMargin(0.02);
  upper->SetFrameFillStyle(0);
  upper->SetFrameLineStyle(0);
  upper->SetFrameLineWidth(2);
  upper->SetFrameBorderMode(0);
  upper->SetFrameBorderSize(10);
  upper->SetFrameFillStyle(0);
  upper->SetFrameLineStyle(0);
  upper->SetFrameLineWidth(2);
  upper->SetFrameBorderMode(0);
  upper->SetFrameBorderSize(10);

  //Drawing histogram
  data_obs->Draw("e1");
  ZEE->Draw("sameh");
  ZJ->Draw("sameh");
  VV->Draw("sameh");
  TT->Draw("sameh");
  if(W!=NULL) {W->Draw("sameh");}
  if(QCD)QCD->Draw("sameh");
  data_obs->Draw("e1same");
  bkgdErr->Draw("e2same");
  //Calculating chi2
  float chi2 = 0;
  for (int iB=1; iB<=nBins; ++iB) 
    {
      float xData = data_obs->GetBinContent(iB);
      float xMC = ZEE->GetBinContent(iB);
      if (xMC>1e-1) 
	{
	  float diff2 = (xData-xMC)*(xData-xMC);
	  chi2 += diff2/xMC;
	}
    }
  std::cout << std::endl;
  std::cout << "Chi2 = " << chi2 << std::endl;
  std::cout << std::endl;

  float x1Leg = 0.70;
  float x2Leg = 0.95;
  if (legLeft) 
    {
      x1Leg = 0.20;
      x2Leg = 0.45;
    }
  TLegend * leg = new TLegend(x1Leg,0.6,x2Leg,0.88);
  SetLegendStyle(leg);
  leg->SetTextSize(0.05);
  leg->AddEntry(data_obs,"Data","lp");
  leg->AddEntry(VV,"Dibosons","f");
  leg->AddEntry(W,"WJets","f");
  leg->AddEntry(QCD,"QCD","f");
  leg->AddEntry(TT,"t#bar{t}","f");
  leg->AddEntry(ZJ,"DY others","f");
  leg->AddEntry(ZEE,"Z#rightarrow ee","f");
  leg->Draw();
  //plotchannel("e#mu");
  //if (!applyPU) suffix = "_noPU";

  //SET YOUR LUMI HERE !!!!!!
  TLatex * cms;
  if(era == "UL2017")  cms = new TLatex(0.65,0.94,"L = 41.86 fb^{-1} at #sqrt{s} = 13 TeV");//UL17
  else if(era == "UL2018")  cms = new TLatex(0.65,0.94,"L = 59.8 fb^{-1} at #sqrt{s} = 13 TeV");//UL18
  else if(era == "UL2016_preVFP")  cms = new TLatex(0.65,0.94,"L = 19.5 fb^{-1} at #sqrt{s} = 13 TeV");//UL16_preVFP
  else if(era == "UL2016_postVFP")  cms = new TLatex(0.65,0.94,"L = 16.8 fb^{-1} at #sqrt{s} = 13 TeV");//UL16_postVFP
  else  cms = new TLatex(0.65,0.94,"L = 59.9 fb^{-1} at #sqrt{s} = 13 TeV");
  //TLatex * cms = new TLatex(0.65,0.94,"L = 59.9 fb^{-1} at #sqrt{s} = 13 TeV");
  //TLatex * cms = new TLatex(0.65,0.94,"L = 41.86 fb^{-1} at #sqrt{s} = 13 TeV");//UL17
  //TLatex * cms = new TLatex(0.65,0.94,"L = 59.8 fb^{-1} at #sqrt{s} = 13 TeV");//UL18
  //TLatex * cms = new TLatex(0.65,0.94,"L = 19.5 fb^{-1} at #sqrt{s} = 13 TeV");//UL16_preVFP
  //TLatex * cms = new TLatex(0.65,0.94,"L = 16.8 fb^{-1} at #sqrt{s} = 13 TeV");//UL16_postVFP

  cms->SetNDC();
  cms->SetTextSize(0.05);
  cms->Draw();
    
  TLatex * cmsLogo = new TLatex(0.20,0.85,"CMS");
  cmsLogo->SetNDC();
  cmsLogo->SetTextSize(0.05);
  cmsLogo->SetTextFont(61);
  cmsLogo->Draw();
    
  TLatex * workinprogress = new TLatex(0.20,0.80,"Work in progress");
  workinprogress->SetNDC();
  workinprogress->SetTextSize(0.05);
  workinprogress->SetTextFont(52);
  workinprogress->Draw();
    
    
  if (logY) upper->SetLogy(true);

  upper->Draw("SAME");
  upper->RedrawAxis();
  upper->Modified();
  upper->Update();
  canv1->cd();
  
  TH1D * ratioH = (TH1D*)data_obs->Clone("ratioH");
  TH1D * ratioErrH = (TH1D*)bkgdErr->Clone("ratioErrH");
  ratioH->SetMarkerColor(1);
  ratioH->SetMarkerStyle(20);
  ratioH->SetMarkerSize(1.5);
  ratioH->SetLineColor(1);
  ratioH->GetYaxis()->SetRangeUser(0.65,1.35);
  ratioH->GetYaxis()->SetNdivisions(505);
  ratioH->GetXaxis()->SetLabelFont(42);
  ratioH->GetXaxis()->SetLabelOffset(0.04);
  ratioH->GetXaxis()->SetLabelSize(0.14);
  ratioH->GetXaxis()->SetTitleSize(0.13);
  ratioH->GetXaxis()->SetTitleOffset(1.2);
  ratioH->GetYaxis()->SetTitle("obs/exp");
  ratioH->GetYaxis()->SetLabelFont(42);
  ratioH->GetYaxis()->SetLabelOffset(0.015);
  ratioH->GetYaxis()->SetLabelSize(0.13);
  ratioH->GetYaxis()->SetTitleSize(0.14);
  ratioH->GetYaxis()->SetTitleOffset(0.5);
  ratioH->GetXaxis()->SetTickLength(0.07);
  ratioH->GetYaxis()->SetTickLength(0.04);
  ratioH->GetYaxis()->SetLabelOffset(0.01);
  
  for (int iB=1; iB<=nBins; ++iB) 
    {
      float x1 = data_obs->GetBinContent(iB);
      float x2 = ZEE->GetBinContent(iB);
      ratioErrH->SetBinContent(iB,1.0);
      ratioErrH->SetBinError(iB,0.0);
      float xBkg = bkgdErr->GetBinContent(iB);
      float errBkg = bkgdErr->GetBinError(iB);
      if (xBkg>0) 
	{
	  float relErr = errBkg/xBkg;
	  ratioErrH->SetBinError(iB,relErr);
	}
      if (x1>0&&x2>0) 
	{
	  float e1 = data_obs->GetBinError(iB);
	  float ratio = x1/x2;
	  float eratio = e1/x2;
	  ratioH->SetBinContent(iB,ratio);
	  ratioH->SetBinError(iB,eratio);
	}
      else 
	{
	  ratioH->SetBinContent(iB,1000);
	}
    }


  TPad *lower = new TPad("lower", "pad",0,0,1,0.30);
  lower->Draw();
  lower->cd();
  lower->SetFillColor(0);
  lower->SetBorderMode(0);
  lower->SetBorderSize(10);
  lower->SetGridy();
  lower->SetTickx(1);
  lower->SetTicky(1);
  lower->SetLeftMargin(0.17);
  lower->SetRightMargin(0.05);
  lower->SetTopMargin(0.026);
  lower->SetBottomMargin(0.35);
  lower->SetFrameFillStyle(0);
  lower->SetFrameLineStyle(0);
  lower->SetFrameLineWidth(2);
  lower->SetFrameBorderMode(0);
  lower->SetFrameBorderSize(10);
  lower->SetFrameFillStyle(0);
  lower->SetFrameLineStyle(0);
  lower->SetFrameLineWidth(2);
  lower->SetFrameBorderMode(0);
  lower->SetFrameBorderSize(10);

  ratioH->Draw("e1");
  ratioErrH->Draw("e2same");
  lower->Modified();
  lower->RedrawAxis();
  canv1->cd();
  canv1->Modified();
  canv1->cd();
  canv1->SetSelected(canv1);
  canv1->Print("./Pre-PostFitPlots/ETauFR_"+era+suffixPassOrFail+eta+wp+suffix+".png");
  canv1->Print("./Pre-PostFitPlots/ETauFR_"+era+suffixPassOrFail+eta+wp+suffix+".pdf","Portrait pdf");
  canv1->Print("macrosOfPlots/ETauFR_"+era+suffixPassOrFail+eta+wp+suffix+".C","cxx");
  canv1->Print("rootFilesOfPlots/ETauFR_"+era+suffixPassOrFail+eta+wp+suffix+".root","root");


}
