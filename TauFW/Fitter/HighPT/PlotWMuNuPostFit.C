#include "HttStylesNew.cc"
#include "CMS_lumi.C"
void PlotWMuNuPostFit(bool postfit = true) {

  SetStyle();
    gStyle->SetErrorX(0);

  TString xtitle = "m_{T} (GeV)";
  TString ytitle = "Events / 100 GeV";

  TString inputFileName("input/munu_mt_1_munu-2018.inputs");
  TString mlfitFileName("fitDiagnostics");

  TFile * inputs = new TFile(inputFileName+".root");
  TFile * mlfit  = new TFile(mlfitFileName+".root"); 

  float yUpper = 7000;

  bool logY = false;

  TString folder("shapes_prefit");
  if (postfit) folder = "shapes_fit_s";

  TH1D * histData = (TH1D*)inputs->Get("WToMuNu/data_obs");
  TH1D * W    = (TH1D*)inputs->Get("WToMuNu/WToMuNu");
  TH1D * Other   = (TH1D*)inputs->Get("WToMuNu/Other");
  TH1D * Wx   = (TH1D*)mlfit->Get(folder+"/WtoMuNu/WToMuNu");
  TH1D * Otherx = (TH1D*)mlfit->Get(folder+"/WtoMuNu/Other");
  TH1D * tot  = (TH1D*)mlfit->Get(folder+"/WtoMuNu/total");

  std::cout << "W     : " << Wx->GetSumOfWeights() << std::endl;
  std::cout << "Other : " << Otherx->GetSumOfWeights() << std::endl;
  std::cout << "EXP : " << tot->GetSumOfWeights() << std::endl;
  std::cout << "DAT : " << histData->GetSumOfWeights() << std::endl;

  TH1D * bkgdErr = (TH1D*)W->Clone("bkgdErr");
  bkgdErr->SetFillStyle(3013);
  bkgdErr->SetFillColor(1);
  bkgdErr->SetMarkerStyle(21);
  bkgdErr->SetMarkerSize(0);  
  
  int nBins = histData->GetNbinsX();

  for (int iB=1; iB<=nBins; ++iB) {
    W->SetBinError(iB,0);
    Other->SetBinError(iB,0);
    W->SetBinContent(iB,tot->GetBinContent(iB));
    Other->SetBinContent(iB,Otherx->GetBinContent(iB));
    bkgdErr->SetBinError(iB,tot->GetBinError(iB));  
    bkgdErr->SetBinContent(iB,tot->GetBinContent(iB));     
  }

  InitData(histData);
  InitHist(Other,"","",TColor::GetColor("#6F2D35"),1001);
  //InitHist(W,"","",TColor::GetColor("#FFCC66"),1001);
  InitHist(W,"","",kYellow,1001);
  histData->GetXaxis()->SetTitle(xtitle);
  histData->GetYaxis()->SetTitle(ytitle);
  histData->GetYaxis()->SetTitleOffset(1.3);
  histData->GetYaxis()->SetTitleSize(0.06);
  histData->GetYaxis()->SetRangeUser(0,yUpper);

  histData->SetMarkerSize(1.2);
  histData->GetXaxis()->SetLabelSize(0);
  histData->GetYaxis()->SetLabelSize(0.06);

  TCanvas * canv1 = MakeCanvas("canv1", "", 700, 800);
  TPad * upper = new TPad("upper", "pad",0,0.31,1,1);
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

  float yMax = 1.2 * histData->GetMaximum();
  histData->GetYaxis()->SetTitle("");
  histData->GetYaxis()->SetRangeUser(0,yMax);    

  histData->Draw("e1");
  W->Draw("sameh");
  Other->Draw("sameh");
  histData->Draw("e1same");
  bkgdErr->Draw("e2same");
  float chi2 = 0;
  for (int iB=1; iB<=nBins; ++iB) {
    float xData = histData->GetBinContent(iB);
    float xMC = W->GetBinContent(iB);
    if (xMC>1e-1) {
      float diff2 = (xData-xMC)*(xData-xMC);
      chi2 += diff2/xMC;
    }
  }
  std::cout << std::endl;
  std::cout << "Chi2 = " << chi2 << std::endl;
  std::cout << std::endl;

  TLegend * leg = new TLegend(0.62,0.4,0.92,0.78);
  SetLegendStyle(leg);
  leg->SetTextSize(0.047);
  leg->AddEntry(histData,"Data","lp");
  leg->AddEntry(W,"W#rightarrow#mu#nu","f");
  leg->AddEntry(Other,"background","f");
  leg->Draw();
  writeExtraText = true;
  extraText = "Work in progress";
  CMS_lumi(upper,4,33); 
  plotchannel("#mu#nu");

  if (logY) upper->SetLogy(true);
    
  upper->Draw("SAME");
  upper->RedrawAxis();
  upper->Modified();
  upper->Update();
  canv1->cd();

  TH1D * ratioH = (TH1D*)histData->Clone("ratioH");
  TH1D * ratioErrH = (TH1D*)bkgdErr->Clone("ratioErrH");
  ratioH->SetMarkerColor(1);
  ratioH->SetMarkerStyle(20);
  ratioH->SetMarkerSize(1.2);
  ratioH->SetLineColor(1);
  ratioH->GetYaxis()->SetRangeUser(0.8001,1.1999);
  ratioH->GetYaxis()->SetNdivisions(505);
  ratioH->GetXaxis()->SetLabelFont(42);
  ratioH->GetXaxis()->SetLabelOffset(0.04);
  ratioH->GetXaxis()->SetLabelSize(0.14);
  ratioH->GetXaxis()->SetTitleSize(0.13);
  ratioH->GetXaxis()->SetTitleOffset(1.2);
  ratioH->GetYaxis()->SetTitle("Obs./Exp.");
  ratioH->GetYaxis()->SetLabelFont(42);
  ratioH->GetYaxis()->SetLabelOffset(0.015);
  ratioH->GetYaxis()->SetLabelSize(0.13);
  ratioH->GetYaxis()->SetTitleSize(0.14);
  ratioH->GetYaxis()->SetTitleOffset(0.5);
  ratioH->GetXaxis()->SetTickLength(0.07);
  ratioH->GetYaxis()->SetTickLength(0.04);
  ratioH->GetYaxis()->SetLabelOffset(0.01);

  for (int iB=1; iB<=nBins; ++iB) {
    float x1 = histData->GetBinContent(iB);
    float x2 = W->GetBinContent(iB);
    ratioErrH->SetBinContent(iB,1.0);
    ratioErrH->SetBinError(iB,0.0);
    float xBkg = bkgdErr->GetBinContent(iB);
    float errBkg = bkgdErr->GetBinError(iB);
    if (xBkg>0) {
      float relErr = errBkg/xBkg;
      ratioErrH->SetBinError(iB,relErr);

    }
    if (x1>0&&x2>0) {
      float e1 = histData->GetBinError(iB);
      float ratio = x1/x2;
      float eratio = e1/x2;
      ratioH->SetBinContent(iB,ratio);
      ratioH->SetBinError(iB,eratio);
    }
    else {
      ratioH->SetBinContent(iB,1000);
    }
  }

  // ------------>Primitives in pad: lower
  TPad * lower = new TPad("lower", "pad",0,0,1,0.30);
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
  canv1->Update();
  canv1->Print("figures/mt1_postfit.png");
   // canv1->Print("figures/"+inputFileName+"_postfit.pdf","Portrait pdf");
  
}
