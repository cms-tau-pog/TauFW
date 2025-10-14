import json
import numpy as np
import re

def Load(file_name):
    with open(file_name) as f:
        trig_desc = json.load(f)
    channel_triggers = {}
    for trig_name, desc in trig_desc.items():
        if 'target_channels' in desc:
            for channel in desc['target_channels']:
                if channel not in channel_triggers:
                    channel_triggers[channel] = []
                desc['name'] = trig_name
                channel_triggers[channel].append(desc)
    return trig_desc, channel_triggers

def LoadAsVPSet(file_name):
    import FWCore.ParameterSet.Config as cms
    with open(file_name) as f:
        trig_desc = json.load(f)
    trig_vpset = cms.VPSet()
    tag_path_names = []
    for trig_name, desc in trig_desc.iteritems():
        filters = [ str(','.join(path_list)) for path_list in desc['filters'] ]
        is_tag = 'is_tag' in desc and desc['is_tag'] > 0
        leg_types = [ str(leg_type) for leg_type in desc['leg_types'] ]
        pset = cms.PSet(
            path = cms.string(str(trig_name)),
            filters = cms.vstring(filters),
            leg_types = cms.vstring(leg_types),
            is_tag = cms.bool(is_tag)
        )
        trig_vpset.append(pset)
        if is_tag:
            tag_path_names.append(str(trig_name))
    return trig_vpset, tag_path_names

def _CreateDictionary(summary, key_name, value_name, name):
    result_dict = {}
    for entry_id in range(len(summary[key_name])):
        keys = np.array(summary[key_name][entry_id])
        values = np.array(summary[value_name][entry_id])
        for n in range(len(keys)):
            if keys[n] in result_dict:
                if result_dict[keys[n]] != values[n]:
                    raise RuntimeError("Inconsistent {} information in the input ROOT files.".format(name))
            else:
                result_dict[keys[n]] = values[n]
    return result_dict

def LoadTriggerDictionary(files):
    import ROOT
    df_support = ROOT.RDataFrame('summary', files)
    summary = df_support.AsNumpy()
    trigger_dict = _CreateDictionary(summary, 'trigger_pattern', 'trigger_index', 'trigger')
    filter_dict = _CreateDictionary(summary, 'filter_name', 'filter_hash', 'filter')
    return trigger_dict, filter_dict

def GetMatchedTriggers(trigger_dict, pattern):
    reg_ex = re.compile(pattern)
    matched = {}
    for name, pos in trigger_dict.items():
        if reg_ex.match(name) is not None:
            matched[name] = pos
    return matched

def GetMatchMask(hlt_paths):
    match_mask = 0
    for path_name, path_index in hlt_paths.items():
        match_mask = match_mask | (1 << path_index)
    return match_mask
