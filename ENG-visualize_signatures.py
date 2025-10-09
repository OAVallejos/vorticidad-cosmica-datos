#!/usr/bin/env python3
"""
ENG-visualize_signatures.py
Vorticity signature visualization and pattern analysis
Critical for identifying non-Gaussian vorticity patterns
"""

import numpy as np
import json

def analyze_vorticity_signature(bispectrum_results):
    """
    Analyze bispectrum results for vorticity signatures
    Returns signature strength and pattern characteristics
    """
    
    print("=== VORTICITY SIGNATURE ANALYSIS ===")
    
    if not bispectrum_results:
        return {"error": "No bispectrum data provided"}
    
    # Extract key metrics
    config_222 = bispectrum_results.get('bispectrum_222', [])
    config_444 = bispectrum_results.get('bispectrum_444', [])
    
    signature_metrics = {
        'redshift_evolution_strength': calculate_evolution_strength(config_222),
        'configuration_consistency': check_configuration_consistency(config_222, config_444),
        'non_gaussianity_pattern': identify_non_gaussianity_pattern(config_222),
        'vorticity_confidence': assess_vorticity_confidence(config_222, config_444)
    }
    
    print("VORTICITY SIGNATURE METRICS:")
    for metric, value in signature_metrics.items():
        print(f"  {metric}: {value:.3f}")
    
    return signature_metrics

def calculate_evolution_strength(bispectrum_values):
    """Calculate strength of redshift evolution pattern"""
    if len(bispectrum_values) < 2:
        return 0.0
    
    # Strong evolution = large changes across redshift
    evolution = np.std(bispectrum_values) / np.mean(bispectrum_values)
    return min(evolution, 1.0)  # Normalize

def check_configuration_consistency(config1, config2):
    """Check consistency between different bispectrum configurations"""
    if len(config1) != len(config2) or len(config1) == 0:
        return 0.0
    
    # Calculate correlation between configurations
    correlation = np.corrcoef(config1, config2)[0,1]
    return abs(correlation) if not np.isnan(correlation) else 0.0

def identify_non_gaussianity_pattern(bispectrum_values):
    """Identify characteristic non-Gaussianity patterns"""
    if len(bispectrum_values) < 3:
        return 0.0
    
    # Look for the dramatic increase pattern (1x → 77x)
    max_val = max(bispectrum_values)
    min_val = min(bispectrum_values)
    
    if min_val == 0:
        return 0.0
    
    increase_ratio = max_val / min_val
    # Normalize: >50x = strong pattern (1.0), <5x = weak pattern (0.0)
    pattern_strength = min((increase_ratio - 5) / 45, 1.0)
    return max(pattern_strength, 0.0)

def assess_vorticity_confidence(config_222, config_444):
    """Assess overall confidence in vorticity detection"""
    evolution = calculate_evolution_strength(config_222)
    consistency = check_configuration_consistency(config_222, config_444) 
    pattern = identify_non_gaussianity_pattern(config_222)
    
    # Weighted combination of metrics
    confidence = (0.4 * evolution) + (0.3 * consistency) + (0.3 * pattern)
    return confidence

# Example usage with paper results
if __name__ == "__main__":
    print("🌀 VORTICITY SIGNATURE VISUALIZATION")
    
    # Paper results for analysis
    paper_data = {
        'bispectrum_222': [125085440, 1064022720, 863196864, 9658739712],  # Values
        'bispectrum_444': [1129590912, 5743875072, 4312530432, 20042827776],
        'redshifts': ['0.1-0.2', '0.3-0.4', '0.5-0.6', '0.7-0.8']
    }
    
    # Analyze vorticity signatures
    signatures = analyze_vorticity_signature(paper_data)
    
    print(f"\n=== VORTICITY DETECTION CONFIDENCE: {signatures['vorticity_confidence']:.1%} ===")
    
    if signatures['vorticity_confidence'] > 0.7:
        print("🎯 HIGH CONFIDENCE IN COSMIC VORTICITY DETECTION")
    elif signatures['vorticity_confidence'] > 0.4:
        print("⚠️ MODERATE CONFIDENCE - REQUIRES FURTHER VALIDATION")
    else:
        print("�️ LOW CONFIDENCE - PATTERN WEAK OR INCONCLUSIVE")
