"""Usage: python 2026-10-22_recording-type-discontinuous.py <bids_root>"""

import hashlib
import json
import sys
import warnings
from pathlib import Path

import mne
import mne_bids
import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def markdown(df: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(map(str, df.columns)) + " |",
        "|" + " --- |" * df.shape[1],
    ]
    lines += [
        "| "
        + " | ".join(f"{v:g}" if isinstance(v, float) else str(v) for v in row)
        + " |"
        for row in df.itertuples(index=False)
    ]
    return "\n".join(lines)


root = Path(sys.argv[1])
rows, hashes, messages = [], [], {}
for sidecar in sorted(root.glob("sub-*/ieeg/*_ieeg.json")):
    meta = json.loads(sidecar.read_text())
    sfreq = meta["SamplingFrequency"]
    vhdr = sidecar.with_suffix(".vhdr")
    events = pd.read_csv(str(sidecar).replace("_ieeg.json", "_events.tsv"), sep="\t")
    durations = events["duration"].to_numpy()
    segments = [
        int(line.split(",")[2]) - 1  # vmrk positions are 1-based
        for line in sidecar.with_suffix(".vmrk").read_text().splitlines()
        if line.startswith("Mk") and "=New Segment," in line
    ]
    plain = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="ERROR")
    entities = mne_bids.get_entities_from_fname(vhdr.name)
    bids_path = mne_bids.BIDSPath(
        root=root, datatype="ieeg", suffix="ieeg", extension=".vhdr", **entities
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            raw = mne_bids.read_raw_bids(bids_path, verbose="WARNING")
            result = "ok"
        except Exception as exc:
            raw, result = None, type(exc).__name__
            messages.setdefault(f"{type(exc).__name__}: {exc}", []).append(
                entities["subject"]
            )
    for w in caught:
        messages.setdefault(f"warning: {str(w.message).splitlines()[0]}", []).append(
            entities["subject"]
        )
    tol = 0.5 / sfreq
    row = {
        "subject": entities["subject"],
        "RecordingType": meta["RecordingType"],
        "EpochLength": meta.get("EpochLength", "absent"),
        "trials": len(events),
        "dur_min_s": durations.min(),
        "dur_median_s": float(np.median(durations)),
        "dur_max_s": durations.max(),
        "distinct_lengths": len(np.unique(durations)),
        "back_to_back": bool(
            np.allclose(events["onset"], np.cumsum(durations) - durations, atol=tol)
            and (events["sample"] == np.round(events["onset"] * sfreq)).all()
            and segments == events["sample"].tolist()
        ),
        "sum_dur_eq_file": bool(
            np.isclose(durations.sum(), plain.n_times / sfreq, atol=2 * tol)
            and np.isclose(
                meta["RecordingDuration"], plain.n_times / sfreq, atol=2 * tol
            )
        ),
        "read_raw_bids": result,
        "warnings": len(caught),
    }
    if raw is not None:
        annot = raw.annotations
        row |= {
            "n_chan": len(raw.ch_names),
            "sfreq": raw.info["sfreq"],
            "n_times": raw.n_times,
            "types": " ".join(
                f"{k}:{v}"
                for k, v in pd.Series(raw.get_channel_types())
                .value_counts()
                .sort_index()
                .items()
            ),
            "bads": len(raw.info["bads"]),
            "annotations": len(annot),
            "annot_eq_events": bool(
                len(annot) == len(events)
                and np.allclose(annot.onset - raw.first_time, events["onset"], atol=tol)
                and np.allclose(annot.duration, durations, atol=tol)
            ),
            "data_eq_plain_read": bool(
                raw.ch_names == plain.ch_names
                and np.array_equal(raw.get_data(), plain.get_data(), equal_nan=True)
            ),
        }
    rows.append(row)
    for path in (vhdr, vhdr.with_suffix(".eeg")):
        hashes.append({"file": str(path.relative_to(root)), "sha256": sha256(path)})

print(f"mne {mne.__version__}, mne_bids {mne_bids.__version__}\n")
print(markdown(pd.DataFrame(rows)), "\n")
print(
    "\n".join(
        f"- {m} (sub {', '.join(sorted(set(s)))})" for m, s in sorted(messages.items())
    ),
    "\n",
)
print(markdown(pd.DataFrame(hashes)))
