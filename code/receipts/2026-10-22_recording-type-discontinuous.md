# Receipt: variable trial lengths, no EpochLength, RecordingType discontinuous

**Claim**: Remove EpochLength and set RecordingType to discontinuous: the 760 trials written back to back vary in length
(5.0-18.0 s), `events.tsv` delimits them, and MNE-BIDS `read_raw_bids` reads all 11 recordings at this head.

**Source**
- NEMAR nm000480 BIDS text files of this commit (`ieeg.json`, `channels.tsv`, `events.tsv`, `.vmrk`, `electrodes.tsv`,
  `coordsystem.json`, `participants.tsv`, `dataset_description.json`), read from a scratch copy of the commit. Against
  `origin/main` 00f02482e148b4376a467524bc88f48b79544492 they differ only in the 11 `ieeg.json` (`RecordingType`
  discontinuous, no `EpochLength`), README, CHANGES, `dataset_description.json` (1.0.3) and `code/receipts/`.
- Binaries (unchanged by this PR): the 22 `.vhdr`/`.eeg` of the NEMAR copy refreshed to `origin/main` on 2026-10-22,
  symlinked into the scratch copy. The sha256 of each (table below) equals the SHA256E key of its git-annex pointer at
  00f0248 (22/22).
- Comparison: the same script on the `origin/main` sidecars (00f0248: `epoched`, `EpochLength` = median trial length) and
  on the previous PR head 49b5fff (`epoched`, no `EpochLength`), same binaries.

**Method**
- `2026-10-22_recording-type-discontinuous.py <bids_root>` with Python 3.12, mne 1.13.2, mne_bids 0.20.0
  (`uv run --no-project --python 3.12 --with mne==1.13.2 --with mne_bids==0.20.0 --with pandas`), Slurm.
- From `events.tsv` per recording: trials, min/median/max `duration`, number of distinct durations. `back_to_back`: every
  `onset` equals the sum of the preceding durations (within 0.5 sample), `sample` = round(`onset` x sfreq), and the
  `.vmrk` `New Segment` positions (1-based, minus 1) equal `sample`. `sum_dur_eq_file`: the summed durations and
  `RecordingDuration` both equal `n_times / sfreq` of the `.eeg` (within 1 sample).
- `mne_bids.read_raw_bids(BIDSPath(subject, task, datatype="ieeg", extension=".vhdr"))`, default arguments: outcome,
  warnings, channels, sfreq, `n_times`, channel types, bads, annotations. `annot_eq_events`: one annotation per
  `events.tsv` row with the same onset and duration (within 0.5 sample). `data_eq_plain_read`: same channel order and
  identical samples as `mne.io.read_raw_brainvision` (NaN-aware; sub-03, sub-06 and sub-10 contain NaN samples), i.e.
  `read_raw_bids` applies no extra scaling.

**Result (this commit)**

| subject | RecordingType | EpochLength | trials | dur_min_s | dur_median_s | dur_max_s | distinct_lengths | back_to_back | sum_dur_eq_file | read_raw_bids | warnings | n_chan | sfreq | n_times | types | bads | annotations | annot_eq_events | data_eq_plain_read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | discontinuous | absent | 76 | 5.01 | 6.1045 | 11.759 | 76 | True | True | ok | 2 | 49 | 1000 | 504725 | ecog:37 seeg:12 | 0 | 76 | True | True |
| 02 | discontinuous | absent | 75 | 5.431 | 6.536 | 11.144 | 72 | True | True | ok | 2 | 49 | 1000 | 523538 | ecog:4 seeg:45 | 0 | 75 | True | True |
| 03 | discontinuous | absent | 80 | 5.153 | 6.4395 | 10.119 | 78 | True | True | ok | 3 | 57 | 1000 | 550940 | seeg:57 | 0 | 80 | True | True |
| 04 | discontinuous | absent | 60 | 5.919 | 7.0735 | 13.042 | 60 | True | True | ok | 2 | 42 | 1000 | 438167 | seeg:42 | 0 | 60 | True | True |
| 05 | discontinuous | absent | 74 | 5.819 | 9.1865 | 15.138 | 74 | True | True | ok | 2 | 43 | 1000 | 717456 | seeg:43 | 0 | 74 | True | True |
| 06 | discontinuous | absent | 69 | 5.52 | 6.384 | 10.352 | 69 | True | True | ok | 2 | 29 | 1000 | 477356 | seeg:29 | 0 | 69 | True | True |
| 07 | discontinuous | absent | 73 | 5.171 | 5.772 | 6.819 | 73 | True | True | ok | 2 | 33 | 1000 | 424129 | seeg:33 | 0 | 73 | True | True |
| 08 | discontinuous | absent | 47 | 5.182 | 5.799 | 6.353 | 46 | True | True | ok | 2 | 20 | 1000 | 270333 | seeg:20 | 0 | 47 | True | True |
| 09 | discontinuous | absent | 73 | 5.245 | 6.191 | 8.625 | 72 | True | True | ok | 2 | 80 | 1000 | 466832 | seeg:80 | 0 | 73 | True | True |
| 10 | discontinuous | absent | 75 | 5.83594 | 7.54492 | 15.1309 | 75 | True | True | ok | 3 | 42 | 512 | 319819 | seeg:42 | 0 | 75 | True | True |
| 11 | discontinuous | absent | 58 | 6.78125 | 9.94824 | 17.9922 | 58 | True | True | ok | 2 | 5 | 512 | 309390 | seeg:5 | 0 | 58 | True | True |

Reader messages at this commit (warnings only, no errors):

- warning: Limited 1 annotation(s) that were expanding outside the data range. (sub 10)
- warning: Other is not an MNE-Python coordinate frame for IEEG data and so will be set to 'unknown' (sub 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11)
- warning: There are channels without locations (n/a) that are not marked as bad: ['G10-G11', 'G11-G12', 'G14-G15', 'G15-G16', 'G17-G18', 'G18-G19', 'G19-G20', 'G20-G21', 'G23-G24'] (sub 03)
- warning: Unable to map the following column(s) to MNE: (sub 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11)

At `origin/main` 00f0248 and at 49b5fff the per-trial columns above are identical (same `events.tsv`), and
`read_raw_bids` raises `RuntimeError: RecordingType is "epoched"; use mne_bids.read_epochs_bids() instead of
read_raw_bids().` for 11/11 recordings.

Binaries read (sha256 = git-annex key at 00f0248):

| file | sha256 |
| --- | --- |
| sub-01/ieeg/sub-01_task-wmgating_ieeg.vhdr | 1fbd0c68721d1259f9279ca11dd4ef52cd2a3c4e17b52efc7c586e8574ec4352 |
| sub-01/ieeg/sub-01_task-wmgating_ieeg.eeg | 3d35bd71170576e716e3cfcd7d32e13bf13cb3e3b66673a000fa66bb69970ecf |
| sub-02/ieeg/sub-02_task-wmgating_ieeg.vhdr | b16c9a0c809b7f49a8aedb6a5df795f34bd76a7e0dc9d0ecd465d15e680ebee3 |
| sub-02/ieeg/sub-02_task-wmgating_ieeg.eeg | 3aad39da80a4452f133e905168fac95f697fbea309664dc90e39ba2e0d42862f |
| sub-03/ieeg/sub-03_task-wmgating_ieeg.vhdr | cf44d5a23a421038b7d7de3686ae0becd734adc599325cdb17e96733729b730c |
| sub-03/ieeg/sub-03_task-wmgating_ieeg.eeg | e3063242b874f2c0fc2c3bdb8181a03da1320c52def31eb7c5eb75fbc9b36236 |
| sub-04/ieeg/sub-04_task-wmgating_ieeg.vhdr | d4731c33934871a47ff86520376a08e8f2892c1a1c6bfa2c328854c58bd0c4b7 |
| sub-04/ieeg/sub-04_task-wmgating_ieeg.eeg | 00722dd82b3d40374e30c2ca225e04272c227ae8c49f078ee656749407982369 |
| sub-05/ieeg/sub-05_task-wmgating_ieeg.vhdr | fcc439ab64d5f6b969912f9d3140198311f57fa8147b322d7349f74483a9fa56 |
| sub-05/ieeg/sub-05_task-wmgating_ieeg.eeg | 49c66cb698383bb78431ea901ae51ccb49c5bb1807d6b2a0bba60fafdbefa3a7 |
| sub-06/ieeg/sub-06_task-wmgating_ieeg.vhdr | b8bb8337531747a6e6afeb4620577b03e53d63a2674e222d38c899f8905b2ea9 |
| sub-06/ieeg/sub-06_task-wmgating_ieeg.eeg | 4b132455aafae4d3c4d679e7a4c3a1a58a174f5154df8ea569885b9c34bdc0ff |
| sub-07/ieeg/sub-07_task-wmgating_ieeg.vhdr | bf3447425646e20b8f3cbac84ad24690c527bfd8d402adfd1facd3e30e0d2b27 |
| sub-07/ieeg/sub-07_task-wmgating_ieeg.eeg | b828bd626cbd19430c16e6a55b8821272d4d022c6570cdf0898724aa267990b5 |
| sub-08/ieeg/sub-08_task-wmgating_ieeg.vhdr | f928cf2c130d1cdba29d111f0f4104396d341fc6de658da3ccd08f102746ab2e |
| sub-08/ieeg/sub-08_task-wmgating_ieeg.eeg | add6935ac3ec84238f99284cf9e06cffc92150a10ca9883e39d58a9ccc4c32d6 |
| sub-09/ieeg/sub-09_task-wmgating_ieeg.vhdr | 6587c14e72a88b80c5dec364699dcebd4661db861f641f518b2a0ff0aab9eebb |
| sub-09/ieeg/sub-09_task-wmgating_ieeg.eeg | c23ffded2cb9c9bc6357b57cd2f85d0c7d656d4bff1f9c58c950fde872e454a7 |
| sub-10/ieeg/sub-10_task-wmgating_ieeg.vhdr | 54a6700bf985c8fbf68a0d2ced684dfd553afeb1e488a444a853d8e496b417f3 |
| sub-10/ieeg/sub-10_task-wmgating_ieeg.eeg | 71a4560f6e264a671e8cea37c72547d4aeaa7147c5d50d978ef7c0c885afc165 |
| sub-11/ieeg/sub-11_task-wmgating_ieeg.vhdr | 6ff222c608c4f6659714a158cf15498210c603ec96673a93722b35fab6843717 |
| sub-11/ieeg/sub-11_task-wmgating_ieeg.eeg | b4ca9973058853b3875dcb37a252e5069d637c940078eb8d1304279ff54c9225 |

**Coverage**: 11 of 11 recordings, 760 of 760 trials, 22 of 22 binaries.
