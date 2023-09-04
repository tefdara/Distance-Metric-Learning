#!/usr/bin/env python3.9
from __future__ import print_function
from essentia.standard import MusicExtractor, YamlOutput
from essentia import Pool
from argparse import ArgumentParser
from utils import flatten_structure
import numpy, os, json, fnmatch, sys, yaml
from termcolor import colored


def add_to_dict(dict, keys, value):
    for key in keys[:-1]:
        dict = dict.setdefault(key, {})
    dict[keys[-1]] = value


def pool_to_dict(pool, ignore_descs=None):
    # a workaround to convert Pool to dict
    descs = pool.descriptorNames()
    if ignore_descs:
        # also look in the nested dicts for keys to ignore from the ignore_descs list
        included_descs = []
        for d in descs:
            keys = d.split('.')
            ignore = False
            # print(f"descs: {d}, keys: {keys}")
            for i in range(len(keys)):
                # print(descs[i])
                if keys[i] in ignore_descs:
                    # print("Ignoring descriptor " + d )
                    ignore = True
                    break
            if not ignore:
                included_descs.append(d)

            descs = included_descs

    result = {}

    for d in descs:
        keys = d.split('.')
        value = pool[d]
        if type(value) is numpy.ndarray:
            value = value.tolist()
        add_to_dict(result, keys, value)
    return result


def extract(audio_file, output_file=None, output_dir=None, profile=None, flatten=False, cache_data=False, cache_dir=None):
    skip_analyzed = False
    ignore_descs = ['analysis', 'bit_rate', 'number_channels', 'sample_rate','codec', 'md5_encoded', 'tags', 'version', 'lossless']
    audio_types = ['*.wav', '*.aiff', '*.aif', '*.flac', '*.mp3', '*.ogg']
    if profile:
        # have to read the profile to get the stats as there is a bug in the MusicExtractor 
        # that does not allow to define the stats in the profile
        default_stats = ['mean', 'var', 'min', 'max', 'dmean', 'dvar', 'dmean2', 'dvar2', 'stdev']
        default_frame_size = 2048
        default_hop_size = 1024
        default_silent_frames = 'noise'
        default_window_type = 'blackmanharris62'
        default_min_tempo = 40
        default_max_tempo = 208
        with open(profile, 'r') as f:
            profile = yaml.safe_load(f)
            analysisSampleRate = float(profile.get('analysisSampleRate', 44100.0))
            lowlevelStats = profile['lowlevel'].get('stats', default_stats)
            lowlevelFrameSize = int(profile['lowlevel'].get('frameSize', default_frame_size))
            lowlevelHopSize = int(profile['lowlevel'].get('hopSize', default_hop_size))
            lowlevelSilentFrames = profile['lowlevel'].get('silentFrames', default_silent_frames)
            tonalStats = profile['tonal'].get('stats', default_stats)
            tonalHopSize = int(profile['tonal'].get('hopSize', default_hop_size))
            tonalFrameSize = int(profile['tonal'].get('frameSize', default_frame_size))
            tonalSilentFrames = profile['tonal'].get('silentFrames', default_silent_frames)
            tonalWindowType = profile['tonal'].get('windowType', default_window_type)
            rhythmStats = profile['rhythm'].get('stats', default_stats)
            rhythmMinTempo = int(profile['rhythm'].get('minTempo', default_min_tempo))
            rhythmMaxTempo = int(profile['rhythm'].get('maxTempo', default_max_tempo))
            indent = int(profile.get('indent', 2))
            loudnessFrameSize = int(analysisSampleRate * 2)
            loudnessHopSize = int(analysisSampleRate)
            outputFrames = int(profile.get('outputFrames', 1))
            store_frames = outputFrames == 1
            ignore_profile = profile.get('ignoreDescriptors', None)
            if ignore_profile:
                ignore_descs = ignore_descs + ignore_profile
        # extractor = MusicExtractor(profile=profile)
        extractor = MusicExtractor(analysisSampleRate=analysisSampleRate, lowlevelStats=lowlevelStats, 
                                   lowlevelFrameSize=lowlevelFrameSize, lowlevelHopSize=lowlevelHopSize, 
                                   lowlevelSilentFrames=lowlevelSilentFrames, tonalStats=tonalStats, 
                                   tonalHopSize=tonalHopSize, tonalFrameSize=tonalFrameSize, 
                                   tonalSilentFrames=tonalSilentFrames, tonalWindowType=tonalWindowType, 
                                   rhythmStats=rhythmStats, rhythmMinTempo=rhythmMinTempo, rhythmMaxTempo=rhythmMaxTempo, 
                                   loudnessFrameSize=loudnessFrameSize, loudnessHopSize=loudnessHopSize)
    else:
        extractor = MusicExtractor()

    errors = 0
    results = {}
    
    print("Analysing %s" % audio_file)
    
    if not output_dir:
        file_dir = os.path.dirname(audio_file)
        output_dir = os.path.join(file_dir, 'analysis')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    sig_file_dir = cache_dir if cache_dir else output_dir
    sig_file = os.path.join(sig_file_dir, audio_file)
    if skip_analyzed:
        if os.path.isfile(sig_file + ".sig"):
            print("Found descriptor file for " + audio_file + ", skipping...")
            return
    try:
        poolStats, poolFrames = extractor(audio_file)
    except Exception as e:
        print("Error processing", audio_file, ":", str(e))
        errors += 1
        return
            
    if not output_file:
        output_file = os.path.join(output_dir, os.path.splitext(audio_file)[0]+'_analysis.json')
        
    results[audio_file] = {}
    results[audio_file]['stats'] = pool_to_dict(poolStats, ignore_descs)
    results = flatten_structure(results)
    if store_frames:
        results[audio_file]['frames'] = pool_to_dict(poolFrames, ignore_descs)

    if cache_data:
        if not os.path.exists(sig_file_dir):
            os.makedirs(sig_file_dir)
        elif os.path.isfile(sig_file_dir):
            raise ValueError("Cannot create folder " + sig_file_dir + " as a file with the same name already exists")
        output = YamlOutput(filename=sig_file+'.sig')
        output(poolStats)
        if store_frames:
            YamlOutput(filename=sig_file + '.frames.sig')(poolFrames)
    print()
    print("Analysis done.", errors, "files have been skipped due to errors")

    data = {'id': audio_file, 'stats': results}
    if os.path.isfile(output_file):
        with open(output_file, 'r') as outfile:
            old_data = json.load(outfile)
            # overwrite the stats with the new ones
            for key in data['stats']:
                if key in old_data['stats'] and old_data['stats'][key] == data['stats'][key]:
                    print(colored("Warning: stats for " + key + " exists with the same value, skipping...", 'yellow'))
                    continue
                print(colored("Warning: stats for " + key + " have been updated", 'yellow'))
                old_data.setdefault('stats', {})[key] = data['stats'][key]
        with open(output_file, 'w') as outfile:
            json.dump(old_data, outfile, indent=4, sort_keys=True)
    else:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=indent, sort_keys=True)


def analyse_folder(dir, output_file=None, output_dir=None, profile=None, flatten=False, cache_data=False, cache_dir=None):
    audio_types = ['*.wav', '*.aiff', '*.aif', '*.flac', '*.mp3', '*.ogg']
    audio_files = []
    for root, dir, filenames in os.walk("."):
        for type in audio_types:
            for filename in fnmatch.filter(filenames, type):
                audio_files.append(os.path.relpath(os.path.join(root, filename)))
    
    for audio_file in audio_files:
        extract(audio_file=audio_file, output_file=output_file, output_dir=output_dir, profile=profile, flatten=flatten, cache_data=cache_data, cache_dir=cache_dir)
                

if __name__ == '__main__':
    dir = os.path.dirname(os.path.realpath(__file__))
    profile = os.path.join(dir, 'profile.yaml')
    parser = ArgumentParser(description = """
        Extracts audio features from a directory of audio files using Essentia MusicExtractor.
    """)
    parser.add_argument('-d', metavar='input_directory', type=str, help='Input directory', required=True)
    parser.add_argument('-o', metavar='output_json_file', type=str, help='Output JSON file', required=False)
    parser.add_argument('-p', metavar='extractor_profile', help='Profile of the extractor, defaults to the profile.yaml file', required=False, default=profile)
    parser.add_argument('-O', metavar='output_directory', type=str, help='Output directory to store descriptor files', required=False)
    parser.add_argument('-f', action='store_true', help='Flatten output dictionary so that all the nested dicts are combined into one', required=False, default=True)
    parser.add_argument('--cache', action='store_true', help='Should raw analysis data be cached', required=False, default=False)
    parser.add_argument('--cache-dir', metavar='cache_directory', type=str, help='Location to save cached data. If none provided, the data will be save in the analysis folder', required=False, default=None)
    
    args = parser.parse_args()
    if(args.cache_dir and not args.cache):
        print(colored("Warning: cache directory provided but caching is not enabled. Ignoring cache directory."), 'yellow')
        args.cache_dir = None
    analyse_folder(args.d, args.o, args.O, args.p, args.f, args.cache, args.cache_dir)
