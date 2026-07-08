# Label Harmonization

Source datasets expose dataset-specific attack names. The public artifact normalizes those native names into seven task families: `benign`, `botnet_c2`, `bruteforce`, `dos`, `other_attack`, `scan_recon`, and `web_attack`.

`docs/label_harmonization.csv` records deterministic rules for UNSW, CICIDS, and MQCIDS labels. Rules are applied in dataset scope first and then through the public fallback rule for attack labels outside the named families. The reference script lowercases labels, removes common attack-prefix text, treats spaces and hyphens consistently, and applies the listed public patterns.

These rules are intended for evaluator-supplied tables that already expose a native label column. They document the stable public task families without packaging raw label tables.
