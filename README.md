Cosmic Vorticity Discovery 🌌🌀

Strong Redshift Evolution of Non-Gaussian Vorticity in Galaxy Velocity Fields: Bispectral Evidence for Beyond-$\Lambda$CDM Physics from 2.8M SDSS and DESI Galaxies


📄 Preprints

Versión

State

DOI

Main Changes

V1.0

Initial Release

10.5281/zenodo.17304825
(https://zenodo.org/records/17304825)

Initial analysis, $\sim 5\sigma$ significance

V2.0

Critical Correction

10.5281/zenodo.17353239
(https://zenodo.org/records/17353239)

Mathematical error correction, $6.99\sigma$ significance

V3.0

Current Version

10.5281/zenodo.17401981
(https://zenodo.org/records/17401981)

DESI + SDSS Analysis, $8.08\sigma$ maximum


🚨 CRITICAL UPDATES ACROSS VERSIONS


V1.0 → V2.0 Transition: Mathematical Correction

Metric

V1.0 State

Corrected V2.0 State

Mathematical Error

Incorrect 3-j symbol implementation

✅ Corrected: Precise Wigner implementation

Robustness Samples

5 bootstrap samples

✅ Improved Robustness: 25 samples

Significance

$\sim 5\sigma$ (initial estimate)

✅ $6.99\sigma$ (Scalene configurations)

Quality Cut

VDISP > 50 km/s

✅ VDISP > 100 km/s (high confidence)


V2.0 → V3.0 Transition: Multi-Survey Validation

Metric

SDSS Only

SDSS + DESI

Maximum Significance

$6.99\sigma$

$8.08\sigma$ (DESI Mass Test)

Cross-Validation

-

$6.25\sigma$ independent confirmation

Galaxies Analyzed

2.8M

5.1M total

Mass Threshold

SDSS Confirmed

Multi-experiment Confirmed


📊 Abstract

Problem: The $\Lambda$CDM model predicts smooth structure evolution from Gaussian initial conditions.

Method: Bispectral analysis of velocity dispersion (VDISP) in 2.8M SDSS DR17 galaxies and 2.3M DESI LRG galaxies using a corrected open-source Rust/Python pipeline.

Finding: The analysis reveals a non-Gaussian signal incompatible with $\Lambda$CDM at $8.08\sigma$ (Max DESI Mass Test) and $6.99\sigma$ (SDSS Scalene), characterized by a $10.00\pm0.69\times$ increase in non-Gaussianity between $z\sim 0.1$ and $z\sim 0.8$ with a clear mass threshold at $M_{c}\approx 3\times 10^{13} M_{\odot}$.

Interpretation: This dramatic evolution is the signature of primordial vorticity in the early cosmic plasma.

Implication: Requires the extension of $\Lambda$CDM with primordial vector fields and establishes three new fundamental parameters beyond the standard model.


🎯 Main Results V3.0


Statistical Significance

8.08σ - Maximum incompatibility with ΛCDM (DESI mass-selected)

6.99σ - SDSS Scalene configurations

6.25σ - DESI independent confirmation


Non-Gaussianity Evolution


Python



Redshift      Evolution (Factor×)
0.1-0.2       1.00× (Reference)
0.3-0.4       2.20 ± 0.40×
0.5-0.6       4.90 ± 0.55×  
0.7-0.8      10.00 ± 0.69×  # 🚨 Primordial signature


Critical Mass Threshold

Mc​≈3×1013M⊙​ - Vortical phase transition

Exclusive evolution in high-mass systems

SDSS-DESI cross-validation: 2.34× vs 2.37× (1.3% difference)


🔬 Summary of the Audacious Proposal and JWST Observational Tests

The paper proposes a fundamental revision to the Standard Cosmological Model ($\Lambda$CDM) by postulating the existence of non-Gaussian primordial vorticity in the initial conditions of the Universe.


The JWST as a Crucial Verifier


1. Test of Early Massive Galaxy Formation

Prediction: Primordial vorticity reduces massive halo formation time by ∼30%

JWST Test: Abundance of massive galaxies at z>10 vs ΛCDM predictions

Expected Result: Significantly higher number of massive galaxies at extreme redshifts


2. Test of the Critical Mass Threshold ($M_c$)

Prediction: Vorticity effect as a "phase change" only above Mc​

Test JWST: Intrinsic properties (age, stellar formation) in proto-clusters

Expected Result: Abrupt jump in properties near the Mc​ threshold


3. Test of the Tully-Fisher-Vorticity Relation

Prediction: Modification of the mass-velocity relation for massive galaxies

Test JWST: Rotation curves with JWST/NIRSpec (z∼1−4)

Expected Result: +16% velocity excess, slope P≈3.4 (vs standard 4.0)


Generate V3 validation data (40 samples)


Calculate significance (6.99σ)

Data: 2.8M SDSS galaxies + 2.3M DESI galaxies with VDISP > 100 km/s (high confidence cut)


🛠️ Corrected Methodology (V2.0+)

Rust/PyO3 Pipeline with mathematically correct implementation of the 3-j symbol

Quality Cut: VDISP > 100 km/s for high confidence

Robust Validation: 40 samples + multiple configurations

First application of the bispectrum to galactic velocity fields


🔗 Three Pillars of Beyond-$\Lambda$CDM Evidence


1. Cosmological Challenge Pillar

Incompatibility with ΛCDM: 7σ significance

Refined result: 2.70±0.12× in scalar modes

Implication: Beyond-ΛCDM Physics confirmed


2. Localization Pillar

Refutation of Malmquist Bias: Signal confined to high mass

Null evolution (∼1.07×) in 2/3 of the low/medium mass population

Conclusion: Localized physical phenomenon, not an artifact


3. Signal Purity Pillar

VDISP Quality Control: Stable signal with strict 150 km/s cut

Consistent significance >6.4σ with improved cut

Conclusion: Vorticity as an intrinsic property of massive systems

# V3 

40 Sample
All test0 1.1x


🤝 Open Source Collaboration


For Developers

# Compile Rust module
cd rust
cargo build --release


For Cosmologists

# method test.
●ANALISIS_SENSIBILIDAD_VDISP.py


# SDSS Robust Test.

●ANALISIS_ROBUSTEZ_MASA_FINAL.py

●VALIDACION_CON_RUST_OPTIMIZADO.py (important)

●ANÁLISIS_ROBUSTEZ_EXTENDIDO.py (important)


# DESI

● ROBUSTEZ_MASA_DESI.py

● VALIDACION_DESI_RUST_LRG.py

Validate with different bispectral configurations


🗓️ Roadmap

[ ] Analysis with additional scalene configurations

[ ] JWST data integration

[ ] CUDA implementation for GPU acceleration

[ ] Analysis of early LSST data


📄 Citation


Fragmento de código



@article{vallejos2025vorticidad,
  title={Strong Redshift Evolution of Non-Gaussian Vorticity in Galaxy Velocity Fields: 
         Bispectral Evidence for Beyond-ΛCDM Physics from 2.8M SDSS and DESI Galaxies},
  author={Vallejos, Omar Ariel},
  journal={Preprint V3},
  year={2025},
  doi={10.5281/zenodo.17401981}
}

Repository: https://github.com/OAVallejos/vorticidad-cosmica-datos


🌟 Acknowledgements

This project uses:

SDSS DR17 and DESI LRG for galactic data

Rust/PyO3 for high-performance computing

DeepSeek for open-source AI research assistance

Gemini (Google AI) for research and code assistance

🌌 Exploring Cosmic Frontiers • 📊 Reproducible Science • 🚀 Open Research

"Science is not only compatible with spirituality; it is a profound source of spirituality." - Carl Sagan
