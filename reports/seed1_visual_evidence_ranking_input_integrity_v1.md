# Seed-1 Visual-Evidence Ranking Input Integrity V1

Status:
- Pass. The frozen candidate registry, all referenced R19 images, and all model
  indexes/shards required by the nine-cell diagnostic were present and readable.
- This audit inspected input identity only. It did not read candidate scores or
  scientific performance values.

Evidence:
- Machine artifact:
  `reports/seed1_visual_evidence_ranking_input_integrity_v1.json`; SHA256
  `e229f3cc613b32ca66647740245de6e1cae2b8113e1a8942591ab0b1d722a232`.
- Frozen config SHA256:
  `6abd53bbf7742167aaf672dcc74633465f7d9378220067c651ce4575375b67bf`.
- Candidate registry: 1,200 unique pairs; SHA256
  `fa9456941a730e174b1ed4bb4caefc151778e3f1adc0ca77db941955a4215f81`.
- R19 images: 2,400 unique paths, 105,880,309 bytes, zero hash mismatches,
  and zero paths outside the frozen R19 release root.
- Base model: two shards, 7,509,337,976 bytes; shard-inventory SHA256
  `6bff2e27c052fc9475f447f744a3dd2a2966e8e0581a2e98d96934b15f9aa5be`.
- A1 step-60 model: two shards, 8,131,668,008 bytes; shard-inventory SHA256
  `6ac699dcdefe378883274903dc6cbde78fbc533b4a84350d4ed952db4593e4c9`.
- A1 step-100 model: two shards, 8,131,668,008 bytes; shard-inventory SHA256
  `bedaa5b6e44290355496413edee6462d9dcf8027296ffc961afc3cbce6a43d06`.
- Adversarial fixture: a tampered or missing registered file fails exact-hash
  matching.
- Focused suite after adding the fixture: `14 passed in 577.79s`; the rerun spent
  most of its elapsed time waiting on shared-filesystem I/O, with no test failure.

Problems:
- The image hashes and model-index hashes were frozen before inference. Full model
  shard inventory hashes were recorded by this audit after the jobs had started;
  they are exact execution provenance, but are not claimed as prospectively
  registered shard hashes.

Decision:
- Treat this machine artifact as a required provenance input to the final diagnostic
  readout. A failed input audit invalidates finalization even if all score cells
  complete.

Next actions:
- Complete all nine immutable scoring cells.
- Finalize the registered estimates and run the independent raw-score recomputation
  audit before opening the result report.
