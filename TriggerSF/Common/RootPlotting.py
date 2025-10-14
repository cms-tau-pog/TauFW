from array import array
import math
import numpy as np
import ROOT

from AnalysisTools import KatzLog

class TextAlign:
    LeftBottom = ROOT.kHAlignLeft + ROOT.kVAlignBottom
    LeftCenter = ROOT.kHAlignLeft + ROOT.kVAlignCenter
    LeftTop = ROOT.kHAlignLeft + ROOT.kVAlignTop
    CenterBottom = ROOT.kHAlignCenter + ROOT.kVAlignBottom
    Center = ROOT.kHAlignCenter + ROOT.kVAlignCenter
    CenterTop = ROOT.kHAlignCenter + ROOT.kVAlignTop
    RightBottom = ROOT.kHAlignRight + ROOT.kVAlignBottom
    RightCenter = ROOT.kHAlignRight + ROOT.kVAlignCenter
    RightTop = ROOT.kHAlignRight + ROOT.kVAlignTop



def ApplyDefaultGlobalStyle():
    ROOT.gStyle.SetPaperSize(20, 20)
    ROOT.gStyle.SetPalette(1)
    ROOT.gStyle.SetEndErrorSize(0)
    ROOT.gStyle.SetPadGridX(False)
    ROOT.gStyle.SetPadGridY(False)
    ROOT.gStyle.SetPadTickX(False)
    ROOT.gStyle.SetPadTickY(False)
    ROOT.gStyle.SetTickLength(0.03, "X")
    ROOT.gStyle.SetTickLength(0.03, "Y")
    ROOT.gStyle.SetNdivisions(510, "X")
    ROOT.gStyle.SetNdivisions(510, "Y")
    ROOT.gStyle.SetOptStat(0)

def ApplyDefaultLineStyle(obj, color):
    obj.SetMarkerSize(4)
    obj.SetMarkerColor(color)
    obj.SetLineWidth(2)
    obj.SetLineColor(color)

def ApplyDefaultLineStyleMarker(obj, color, marker):
    obj.SetMarkerStyle(marker)
    # obj.SetMarkerSize(4)
    obj.SetMarkerColor(color)
    obj.SetLineWidth(2)
    obj.SetLineColor(color)

def ApplyAxisSetup(frame_hist, ratio_frame_hist=None, x_title="", y_title="", ratio_y_title="",
                   axis_title_sizes=(0.055, 0.055), axis_title_offsets=(1,1.4), axis_label_sizes=(0.04,0.04),
                   axis_label_offsets=(0.005,0.005), ratio_item_size_sf=2.76, max_ratio=1.5, ratio_y_title_size=0.055,
                   ratio_y_title_offset=0.4, ratio_y_label_size=0.04, ratio_y_label_offset=0.005, ratio_n_div_y=505,
                   y_range=None):
    frame_hist.GetYaxis().SetTitle(y_title)
    frame_hist.GetYaxis().SetTitleSize(axis_title_sizes[1])
    frame_hist.GetYaxis().SetTitleOffset(axis_title_offsets[1])
    frame_hist.GetYaxis().SetLabelSize(axis_label_sizes[1])
    frame_hist.GetYaxis().SetLabelOffset(axis_label_offsets[1])
    if y_range is not None:
        frame_hist.GetYaxis().SetRangeUser(*y_range)
    if ratio_frame_hist is not None:
        frame_hist.GetXaxis().SetTitle("")
        frame_hist.GetXaxis().SetTitleSize(0)
        frame_hist.GetXaxis().SetTitleOffset(0)
        frame_hist.GetXaxis().SetLabelSize(0)
        frame_hist.GetXaxis().SetLabelOffset(0)

        ratio_frame_hist.GetXaxis().SetTitle(x_title)
        ratio_frame_hist.GetXaxis().SetTitleSize(axis_title_sizes[0] * ratio_item_size_sf)
        ratio_frame_hist.GetXaxis().SetTitleOffset(axis_title_offsets[0])
        ratio_frame_hist.GetXaxis().SetLabelSize(axis_label_sizes[0] * ratio_item_size_sf)
        ratio_frame_hist.GetXaxis().SetLabelOffset(axis_label_offsets[0])
        ratio_frame_hist.GetXaxis().SetNoExponent(True)
        ratio_frame_hist.GetXaxis().SetMoreLogLabels(True)

        ratio_frame_hist.GetYaxis().SetTitle(ratio_y_title)
        ratio_frame_hist.GetYaxis().SetTitleSize(ratio_y_title_size * ratio_item_size_sf)
        ratio_frame_hist.GetYaxis().SetTitleOffset(ratio_y_title_offset)
        ratio_frame_hist.GetYaxis().SetLabelSize(ratio_y_label_size * ratio_item_size_sf)
        ratio_frame_hist.GetYaxis().SetLabelOffset(ratio_y_label_offset)
        ratio_frame_hist.GetYaxis().SetNdivisions(ratio_n_div_y);
        if max_ratio > 0:
            ratio_frame_hist.GetYaxis().SetRangeUser(max(0., 2 - max_ratio), max_ratio)
    else:
        frame_hist.GetXaxis().SetTitle(x_title);
        frame_hist.GetXaxis().SetTitleSize(axis_title_sizes[0])
        frame_hist.GetXaxis().SetTitleOffset(axis_title_offsets[0])
        frame_hist.GetXaxis().SetLabelSize(axis_label_sizes[0])
        frame_hist.GetXaxis().SetLabelOffset(axis_label_offsets[0])
        frame_hist.GetXaxis().SetNoExponent(True)
        frame_hist.GetXaxis().SetMoreLogLabels(True)

def CreateCanvas(size_x=700, size_y=700):
    canvas = ROOT.TCanvas('', '', size_x, size_y)
    canvas.SetFillColor(ROOT.kWhite)
    canvas.SetBorderSize(10)
    canvas.SetBorderMode(0)
    return canvas

class Box:
    def __init__(self, left_bottom_x, left_bottom_y, right_top_x, right_top_y):
        self.left_bottom_x = left_bottom_x
        self.left_bottom_y = left_bottom_y
        self.right_top_x = right_top_x
        self.right_top_y = right_top_y

    def __iter__(self):
        return iter((self.left_bottom_x, self.left_bottom_y, self.right_top_x, self.right_top_y))

class MarginBox:
    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

def SetMargins(main_pad, margin_box, ratio_pad=None, ratio_pad_y_size_sf=2.76, main_ratio_margin=0.04):
    main_pad.SetLeftMargin(margin_box.left)
    main_pad.SetRightMargin(margin_box.right)
    main_pad.SetTopMargin(margin_box.top)
    if ratio_pad is not None:
        ratio_pad.SetLeftMargin(margin_box.left)
        ratio_pad.SetRightMargin(margin_box.right)
        ratio_pad.SetBottomMargin(margin_box.bottom * ratio_pad_y_size_sf);
        ratio_pad.SetTopMargin(main_ratio_margin / 2 * ratio_pad_y_size_sf);
        main_pad.SetBottomMargin(main_ratio_margin / 2)
    else:
        main_pad.SetBottomMargin(margin_box.bottom)

def DrawLabel(text, pos, text_size=0.05, font=42, align=TextAlign.Center, angle=0, color=ROOT.kBlack,
              line_spacing=1):
    x = pos[0]
    y = pos[1]
    alpha = math.radians(angle)
    sin_alpha = math.sin(alpha)
    cos_alpha = math.cos(alpha)

    label_controls = []
    for line in text.split('\n'):
        latex = ROOT.TLatex(x, y, line)
        latex.SetNDC()
        latex.SetTextSize(text_size)
        latex.SetTextFont(font)
        latex.SetTextAlign(align)
        latex.SetTextAngle(angle)
        latex.SetTextColor(color)
        latex.Draw("SAME")
        label_controls.append(latex)
        shift_x = 0
        shift_y = -(1 + line_spacing) * latex.GetYsize()
        x += shift_x * cos_alpha + shift_y * sin_alpha
        y += -shift_x * sin_alpha + shift_y * cos_alpha
    return label_controls

def CreateTwoPadLayout(canvas, ref_hist, ratio_ref_hist, main_box=Box(0.02, 0.25, 0.95, 0.94),
                       margins=MarginBox(0.15, 0.14, 0.03, 0.02), ratio_pad_size=0.25, log_x=False, log_y=False,
                       title='', title_pos=(0.5, 0.96), title_text_size=0.05, title_font=42, title_color=ROOT.kBlack):
    canvas.cd()
    ratio_box = Box(main_box.left_bottom_x, main_box.left_bottom_y - ratio_pad_size,
                    main_box.right_top_x, main_box.left_bottom_y)
    main_pad = ROOT.TPad('', '', *main_box)
    ratio_pad = ROOT.TPad('', '', *ratio_box)
    SetMargins(main_pad, margins, ratio_pad)

    main_pad.Draw()
    ratio_pad.Draw()

    main_pad.cd()
    main_pad.SetLogx(log_x)
    main_pad.SetLogy(log_y)
    ref_hist.Draw()
    ref_hist.SetTitle('')

    ratio_pad.cd()
    ratio_pad.SetLogx(log_x)
    ratio_pad.SetGridy()
    ratio_ref_hist.Draw()
    ratio_ref_hist.SetTitle('')

    canvas.cd()
    if title is not None and len(title) > 0:
        canvas.SetTitle(title)
        title_controls = DrawLabel(title, pos=title_pos, text_size=title_text_size, font=title_font,
                                   align=TextAlign.Center, color=title_color)
    else:
        title_controls = None

    main_pad.cd()
    return main_pad, ratio_pad, title_controls

def CreateLegend(pos=(0.18, 0.78), size=(0.2, 0.15), fill_color=ROOT.kWhite, fill_style=0, border_size=0,
                 text_size=0.04, font=42):
    legend = ROOT.TLegend(pos[0], pos[1], pos[0] + size[0], pos[1] + size[1])
    legend.SetFillColor(fill_color)
    legend.SetFillStyle(fill_style)
    legend.SetBorderSize(border_size)
    legend.SetTextSize(text_size)
    legend.SetTextFont(font)

    return legend


def CreateEfficiencyRatioGraph(hist_passed_a, hist_total_a, hist_passed_b, hist_total_b):
    n_bins = hist_passed_a.GetNbinsX()
    x = np.zeros(n_bins)
    y = np.zeros(n_bins)
    exl = np.zeros(n_bins)
    exh = np.zeros(n_bins)
    eyl = np.zeros(n_bins)
    eyh = np.zeros(n_bins)

    k = 0
    for n in range(n_bins):
        passed_a = hist_passed_a.GetBinContent(n + 1)
        total_a = hist_total_a.GetBinContent(n + 1)
        passed_b = hist_passed_b.GetBinContent(n + 1)
        total_b = hist_total_b.GetBinContent(n + 1)
        if total_a == 0 or total_b == 0 or passed_a == 0 or passed_b == 0: continue

        x[k] = hist_passed_a.GetBinCenter(n + 1)
        exl[k] = hist_passed_a.GetBinWidth(n + 1) / 2
        exh[k] = exl[k]
        y_down, y_up = KatzLog(np.array([passed_a, passed_b]), np.array([total_a, total_b]))
        y[k] = (passed_a * total_b) / (passed_b * total_a)
        eyl[k] = y_up - y[k]
        eyh[k] = y[k] - y_down
        k += 1
    if k == 0:
        return None
    return ROOT.TGraphAsymmErrors(k, array('d', x), array('d', y), array('d', exl), array('d', exh),
                                  array('d', eyl), array('d', eyh))

def GetPrintSuffix(current_page_number, total_number_of_pages):
    print_suffix = ''
    if total_number_of_pages > 1:
        if current_page_number == 0:
            print_suffix = '('
        elif current_page_number == total_number_of_pages - 1:
            print_suffix = ')'
    return print_suffix

def PrintAndClear(canvas, file, title, current_page_number, total_number_of_pages, dm, pads = []):
    canvas.Print(file + GetPrintSuffix(current_page_number, total_number_of_pages),
                 'Title:{}'.format(title))
    canvas.SaveAs(file[:-4] + "{}.png".format(dm))
    for pad in pads:
        pad.Clear()
    canvas.Clear()

def GetYRange(curves, consider_errors=True):
    y_values = []
    for curve in curves:
        if type(curve) == ROOT.TH1D:
            for bin_id in range(1, curve.GetNbinsX() + 1):
                y = curve.GetBinContent(bin_id)
                if consider_errors:
                    y_values.append(y - curve.GetBinErrorLow(bin_id))
                    y_values.append(y + curve.GetBinErrorUp(bin_id))
                else:
                    y_values.append(y)
        elif type(curve) == ROOT.TGraphAsymmErrors:
            for n in range(curve.GetN()):
                y = curve.GetY()[n]
                if consider_errors:
                    y_values.append(y - curve.GetEYlow()[n])
                    y_values.append(y + curve.GetEYhigh()[n])
                else:
                    y_values.append(y)
        else:
            raise RuntimeError('GetYRange: type = "" is not supported.'.format(type(curve)))
    return min(y_values), max(y_values)

def DivideByBinWidth(hist):
    for n in range(1, hist.GetNbinsX() + 1):
        new_value = hist.GetBinContent(n) / hist.GetBinWidth(n);
        new_bin_error = hist.GetBinError(n) / hist.GetBinWidth(n);
        hist.SetBinContent(n, new_value);
        hist.SetBinError(n, new_bin_error);

def HistogramToGraph(hist):
    n_bins = hist.GetNbinsX()
    x = np.zeros(n_bins)
    y = np.zeros(n_bins)
    exl = np.zeros(n_bins)
    exh = np.zeros(n_bins)
    eyl = np.zeros(n_bins)
    eyh = np.zeros(n_bins)

    k = 0
    for n in range(n_bins):
        bin_y = hist.GetBinContent(n + 1)
        bin_y_err_low = hist.GetBinErrorLow(n + 1)
        bin_y_err_up = hist.GetBinErrorUp(n + 1)
        if bin_y == 0 and bin_y_err_low == 0 and bin_y_err_up == 0: continue

        x[k] = hist.GetBinCenter(n + 1)
        exl[k] = hist.GetBinWidth(n + 1) / 2
        exh[k] = exl[k]
        y[k] = bin_y
        eyl[k] = bin_y_err_low
        eyh[k] = bin_y_err_up
        k += 1
    if k == 0:
        return None

    return ROOT.TGraphAsymmErrors(k, array('d', x), array('d', y), array('d', exl), array('d', exh),
                                array('d', eyl), array('d', eyh))
