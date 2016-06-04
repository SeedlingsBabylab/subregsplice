# subregsplice

This script slices an audio track into component subregions, then combines
these subregions into a new concatenated audio file. A corresponding .cha file
will be produced with new timestamps to reflect the new positions of the subregions
within the concatenated audio file. 

Each subregion will have an associated comment describing the displacement in time
required to produce the original timestamps. 

## usage

```
$: python subrsplice.py [original_cha_file.cha] [list_of_subregions.csv] [audio_file.wav] [output_dir]
```
