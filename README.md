Cosmic Vorticity Discovery 🌌🌀

Strong Redshift Evolution of Non-Gaussianity in Galaxy Velocity Dispersion: Bispectral Evidence for Beyond-ΛCDM Physics from 2.8M SDSS Galaxies

📄 Preprint (v1): 
https://doi.org/10.5281/zenodo.17304825

📄 Preprint (v2): https://doi.org/10.5281/zenodo.17353239

🚨 CRITICAL UPDATES AND CORRECTIONS (V2)

This version updates the V1.0 preprint to incorporate the correction of a systematic mathematical error and to improve statistical robustness.

Metric

Previous Status (V1.0)

Corrected Status (V2)

Mathematical Error

Incorrect 3-j symbol implementation

✅ Corrected: Precise Wigner implementation

Robustness Sampling

5 bootstrap samples

✅ Improved Robustness: 25 samples

Significance

~5σ (initial estimate)

✅ 6.99σ (Scalenes) vs. ΛCDM prediction

Quality Cut

VDISP > 50 km/s

✅ VDISP > 100 km/s (high confidence)


📊 Abstract

Analysis of 2.8 million SDSS DR17 galaxies reveals:

Significance: 6.99σ incompatibility with ΛCDM
Evolution: 10.00±0.69× in non-Gaussianity (z=0.1 to z=0.8)
Interpretation: Evidence for primordial vorticity
Implication: Requires beyond-ΛCDM physics with vector fields

🚀 Reproduction

Main Analysis:


Bash



# Generate validation data (25 samples)
python3 VALIDACION_CON_RUST_OPTIMIZADO.py

# Calculate significance (6.99σ)
python3 CALCULO_SIGNIFICANCIA_CORREGIDO.py

Data: 2.8M SDSS galaxies with VDISP > 100 km/s (high confidence cut)


📁 Repository Structure




vorticidad-cosmica-datos/
├── CALCULO_SIGNIFICANCIA_CORREGIDO.py       # 🆕 6.99σ Calculation
├── VALIDACION_CON_RUST_OPTIMIZADO.py        # 🆕 Data Generator
├── analisis_divergencia_OPTIMIZADO.json     # 🆕 25 Validated Samples
├── rust/                                    # Corrected Rust Pipeline
├── datasets/                                # Processed SDSS Data
└── cosmic_vorticity_paper.pdf               # Preprint V1.0


🔬 Final Results (V2)

Principal Significance: 6.99σ (scalene configurations)
Evolution: 10.00±0.69× (z=0.1-0.8)
Incompatibility: 9.1× larger than ΛCDM
Samples: 25 bootstrap validations
Galaxies: 2.8M with VDISP > 100 km/s

🎯 Corrected Methodology

Rust/PyO3 Pipeline with mathematically correct 3-j symbol
Quality Cut: VDISP > 100 km/s for high confidence
Robust Validation: 25 samples + multiple configurations
First application of the bispectrum to galaxy velocity fields

🤝 Open Source Collaboration


For Developers:


Bash



# Compile Rust module
cd rust
cargo build --release

# Run validation tests
python3 VALIDACION_CON_RUST_OPTIMIZADO.py


For Cosmologists:

Review CALCULO_SIGNIFICANCIA_CORREGIDO_V2.py for statistical methodology
Analyze analisis_divergencia_OPTIMIZADO.json for raw data
Validate with different bispectral configurations

How to Contribute:

Report issues on GitHub
Propose improvements to the Rust/Python pipeline
Validate results with alternative datasets
Extend analysis to other surveys (DESI, LSST)

Roadmap:

[ ] Analysis with additional scalene configurations
[ ] JWST data integration
[ ] CUDA implementation for GPU acceleration

📄 Citation


Fragmento de código



@article{vallejos2025vorticidad,
 title={Strong Redshift Evolution of Non-Gaussianity in Galaxy Velocity Fields},
 author={Vallejos, Omar Ariel},
 journal={Preprint v2},
 year={2025},
 doi={10.5281/zenodo.17353239}
}

🔗 Repository: https://github.com/OAVallejos/vorticidad-cosmica-datos


🌟 Acknowledgments

This project uses:

SDSS DR17 for galactic data
Rust/PyO3 for high-performance computing
DeepSeek for research assistance with open source AI and Gemini (Google AI) for research and code assistance, including optimization of the Rust/Python pipeline.

🌌 Exploring Cosmic Frontiers • 📊 Reproducible Science • 🚀 Open Research

"Science is not only compatible with spirituality; it is a profound source of spirituality." - Carl Sagan
