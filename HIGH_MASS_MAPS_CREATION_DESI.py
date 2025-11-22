#!/usr/bin/env python3
"""                   
Creates HEALPix Nside=64 maps for density/vorticity for the High Mass group at high redshift
"""

import numpy as np
import healpy as hp
from astropy.table import Table
import matplotlib.pyplot as plt
import os
from tqdm import tqdm

def calculate_healpix_gradient(healpix_map, nside):
    """Calculates the gradient of a HEALPix map using finite differences"""
    npix = len(healpix_map)
    grad_theta = np.zeros(npix)
    grad_phi = np.zeros(npix)
    
    for ipix in range(npix):
        # Get pixel neighbors
        neighbors = hp.get_all_neighbours(nside, ipix)
        
        # Central pixel coordinates
        theta, phi = hp.pix2ang(nside, ipix)
        
        # Neighbor values (use 0.0 if neighbor doesn't exist, typical at edges/mask)
        neighbor_values = []
        for neighbor in neighbors:
            if neighbor >= 0 and neighbor < npix:
                neighbor_values.append(healpix_map[neighbor])
            else:
                neighbor_values.append(0.0)
        
        # Calculate approximate derivatives
        # Simplification: use differences between opposite neighbors
        if len(neighbor_values) >= 4:
            # Derivative in theta (North-South direction)
            dtheta = (neighbor_values[2] - neighbor_values[0]) / (2 * hp.nside2resol(nside))
            # Derivative in phi (East-West direction)
            # Note: normalized by sin(theta) for spherical metric
            dphi = (neighbor_values[1] - neighbor_values[3]) / (2 * hp.nside2resol(nside) * np.sin(theta))
            
            grad_theta[ipix] = dtheta
            grad_phi[ipix] = dphi
    
    return grad_theta, grad_phi

def create_high_mass_maps():
    print("🗺️ HEALPix MAP CREATION FOR HIGH MASS (high_z)")
    print("=====================================================")

    # HEALPix Configuration
    NSIDE = 64
    NPIX = hp.nside2npix(NSIDE)
    print(f"🔧 HEALPix Configuration: Nside={NSIDE}, Npix={NPIX}")

    # 1. Load DESI data
    try:
        desi_table = Table.read('DATASET_LRG_VDISP_FLUXR_FINAL.fits')
        vdisp_desi = np.array(desi_table['VDISP'])
        redshift_desi = np.array(desi_table['Z'])
        ra_desi = np.array(desi_table['RA'])   # Right Ascension (degrees)
        dec_desi = np.array(desi_table['DEC']) # Declination (degrees)
        print(f"✅ DESI data loaded: {len(vdisp_desi):,} galaxies")
    except FileNotFoundError:
        print("❌ Error: Could not load DESI dataset")
        return None, None

    # 2. Define groups based on tuning
    MC_THRESHOLD = 220.0  # km/s - result from tuning
    HIGH_Z_MIN, HIGH_Z_MAX = 0.8, 1.0  # High redshift bin

    print(f"\n🎯 GALAXY SELECTION:")
    print(f"   • High Mass: VDISP > {MC_THRESHOLD} km/s")
    print(f"   • High Redshift: z = {HIGH_Z_MIN}-{HIGH_Z_MAX}")

    # 3. Filter High Mass galaxies at high redshift
    mask_high_mass_high_z = (vdisp_desi > MC_THRESHOLD) & \
                            (redshift_desi >= HIGH_Z_MIN) & \
                            (redshift_desi < HIGH_Z_MAX)

    ra_selected = ra_desi[mask_high_mass_high_z]
    dec_selected = dec_desi[mask_high_mass_high_z]
    vdisp_selected = vdisp_desi[mask_high_mass_high_z]
    z_selected = redshift_desi[mask_high_mass_high_z]

    n_galaxies = len(ra_selected)
    print(f"   • Selected galaxies: {n_galaxies:,}")
    print(f"   • VDISP range: {vdisp_selected.min():.1f} - {vdisp_selected.max():.1f} km/s")
    print(f"   • Redshift range: {z_selected.min():.3f} - {z_selected.max():.3f}")

    if n_galaxies == 0:
        print("❌ No galaxies meet the criteria")
        return None, None

    # 4. Save table of selected galaxies
    filtered_table = desi_table[mask_high_mass_high_z]
    filtered_table.write('high_mass_galaxies_z08-10.fits', overwrite=True)
    print(f"✅ Filtered galaxy table saved: 'high_mass_galaxies_z08-10.fits'")

    # 5. Convert Equatorial Coordinates (RA, DEC) to HEALPix Spherical Coordinates
    print(f"\n📡 CONVERTING TO HEALPix COORDINATES...")

    # Convert RA, DEC to theta, phi (healpy uses theta [0,pi], phi [0, 2pi])
    # theta = pi/2 - dec (in radians), phi = ra (in radians)
    theta = np.radians(90.0 - dec_selected)  # Colatitude
    phi = np.radians(ra_selected)            # Longitude

    # 6. Assign galaxies to HEALPix pixels
    print("   Assigning galaxies to HEALPix pixels...")
    pixel_indices = hp.ang2pix(NSIDE, theta, phi)

    # 7. Create galaxy count map
    print("   Creating galaxy density map...")
    count_map = np.zeros(NPIX)
    
    # With progress bar
    for i, pix in enumerate(tqdm(pixel_indices, desc="   Processing galaxies")):
        count_map[pix] += 1
        if i % 10000 == 0 and i > 0:  # Progress update every 10000 galaxies
            print(f"      Processed {i}/{n_galaxies} galaxies...")

    # 8. Create normalized density map (galaxies/area)
    pixel_area = hp.nside2pixarea(NSIDE, degrees=True)  # area per pixel in degrees²
    density_map = count_map / pixel_area  # galaxies/degree²

    # 9. Create average VDISP map per pixel
    print("   Creating average VDISP map...")
    map_vdisp_sum = np.zeros(NPIX)
    map_vdisp_count = np.zeros(NPIX)

    for i, pix in enumerate(tqdm(pixel_indices, desc="   Calculating average VDISP")):
        map_vdisp_sum[pix] += vdisp_selected[i]
        map_vdisp_count[pix] += 1

    # Safe division
    vdisp_avg_map = np.divide(map_vdisp_sum, map_vdisp_count,
                              out=np.zeros_like(map_vdisp_sum),
                              where=map_vdisp_count > 0)

    # 10. Calculate density contrast field δ = (ρ - ρ̄)/ρ̄
    print("   Calculating density contrast field δ...")
    mean_density = np.mean(density_map[density_map > 0])
    delta_map = (density_map - mean_density) / mean_density
    delta_map[density_map == 0] = 0  # Where there are no galaxies, δ = 0

    print(f"   • Mean density: {mean_density:.3f} galaxies/degree²")
    print(f"   • Max δ: {delta_map.max():.3f}")
    print(f"   • Min δ: {delta_map.min():.3f}")

    # 11. Calculate gradient of field δ (for vorticity analysis)
    print("   Calculating gradient of field δ (Finite Differences)...")
    # Using custom function instead of hp.grad to handle local variations better
    grad_theta, grad_phi = calculate_healpix_gradient(delta_map, NSIDE)
    
    # Calculate gradient magnitude
    gradient_magnitude = np.sqrt(grad_theta**2 + grad_phi**2)
    
    print(f"   • Max gradient magnitude: {gradient_magnitude.max():.3f}")
    print(f"   • Mean gradient magnitude: {gradient_magnitude[gradient_magnitude > 0].mean():.3f}")

    # 12. Save the maps
    print(f"\n💾 SAVING MAPS...")

    # Create directory if it doesn't exist
    os.makedirs('healpix_maps', exist_ok=True)

    # Save maps in FITS format
    hp.write_map('healpix_maps/galaxy_count_map.fits', count_map, overwrite=True)
    hp.write_map('healpix_maps/galaxy_density_map.fits', density_map, overwrite=True)
    hp.write_map('healpix_maps/vdisp_avg_map.fits', vdisp_avg_map, overwrite=True)
    hp.write_map('healpix_maps/delta_density_map.fits', delta_map, overwrite=True)
    hp.write_map('healpix_maps/delta_gradient_map.fits', gradient_magnitude, overwrite=True)

    # Save gradient components
    hp.write_map('healpix_maps/gradient_theta.fits', grad_theta, overwrite=True)
    hp.write_map('healpix_maps/gradient_phi.fits', grad_phi, overwrite=True)

    # Save metadata
    metadata = {
        'nside': NSIDE,
        'npix': NPIX,
        'mc_threshold': MC_THRESHOLD,
        'high_z_min': HIGH_Z_MIN,
        'high_z_max': HIGH_Z_MAX,
        'n_galaxies': n_galaxies,
        'mean_density': mean_density,
        'max_delta': float(delta_map.max()),
        'min_delta': float(delta_map.min()),
        'max_gradient': float(gradient_magnitude.max()),
        'mean_gradient': float(gradient_magnitude[gradient_magnitude > 0].mean()),
        'description': 'HEALPix Maps for High Mass (VDISP > 220 km/s) at z=0.8-1.0'
    }

    np.savez('healpix_maps/map_metadata.npz', **metadata)

    # Save metadata in readable text
    with open('healpix_maps/map_metadata.txt', 'w') as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")

    print("✅ Maps saved in directory 'healpix_maps/'")

    # 13. Visualize the maps
    print(f"\n🎨 CREATING VISUALIZATIONS...")
    visualize_maps(count_map, density_map, vdisp_avg_map, delta_map, gradient_magnitude, NSIDE)

    return delta_map, gradient_magnitude, metadata, filtered_table

def visualize_maps(count_map, density_map, vdisp_map, delta_map, gradient_magnitude, nside):
    """Creates visualizations of the HEALPix maps"""
    
    # FIX: Removed plt.subplots() to prevent empty axes conflict with healpy
    plt.figure(figsize=(20, 12))
    plt.suptitle('HEALPix Maps - DESI High Mass (VDISP > 220 km/s, z=0.8-1.0)', fontsize=16)

    # Galaxy Count Map
    hp.mollview(count_map, title="Galaxy Count per Pixel",
                unit="N galaxies", sub=(2,3,1), min=0, cmap='viridis')

    # Density Map
    hp.mollview(density_map, title="Galaxy Density",
                unit="galaxies/deg²", sub=(2,3,2), min=0, cmap='plasma')

    # Average VDISP Map
    hp.mollview(vdisp_map, title="Average VDISP",
                unit="km/s", sub=(2,3,3), min=220, cmap='inferno')

    # Density Contrast δ Map
    hp.mollview(delta_map, title="Density Contrast δ",
                unit="(ρ-ρ̄)/ρ̄", sub=(2,3,4), cmap='RdBu_r', min=-1, max=2)

    # Gradient Magnitude Map
    hp.mollview(gradient_magnitude, title="Gradient Magnitude ∇δ",
                unit="|∇δ|", sub=(2,3,5), min=0, cmap='YlOrRd')

    # Log(count+1) Map for better visualization
    log_count_map = np.log10(count_map + 1)
    hp.mollview(log_count_map, title="Log(Count+1) of Galaxies",
                unit="log₁₀(N+1)", sub=(2,3,6), cmap='viridis')

    plt.savefig('healpix_maps/full_map_visualization.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ Visualizations saved as 'healpix_maps/full_map_visualization.png'")

    # Create individual visualization for δ field
    plt.figure(figsize=(12, 8))
    hp.mollview(delta_map, title="Density Contrast Field δ - DESI High Mass\n(VDISP > 220 km/s, z=0.8-1.0)",
                unit="(ρ-ρ̄)/ρ̄", cmap='RdBu_r', min=-1, max=2)
    plt.savefig('healpix_maps/delta_field_high_mass.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Visualization of the gradient
    plt.figure(figsize=(12, 8))
    hp.mollview(gradient_magnitude, title="Gradient Magnitude ∇δ - DESI High Mass\n(Regions of high variation)",
                unit="|∇δ|", cmap='YlOrRd')
    plt.savefig('healpix_maps/delta_gradient_high_mass.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ Individual visualizations saved")

def analyze_vorticity_structures(delta_map, gradient_magnitude, metadata):
    """Preliminary analysis of structures in the δ field (vorticity proxy)"""
    print(f"\n🔍 ANALYSIS OF STRUCTURES IN FIELD δ")
    print("==========================================")

    # Filter only pixels with galaxies
    delta_nonzero = delta_map[delta_map != 0]
    gradient_nonzero = gradient_magnitude[gradient_magnitude > 0]

    if len(delta_nonzero) > 0:
        print(f"   • Pixels with galaxies: {len(delta_nonzero):,}/{len(delta_map):,}")
        print(f"   • Mean δ: {np.mean(delta_nonzero):.3f}")
        print(f"   • Std δ: {np.std(delta_nonzero):.3f}")
        print(f"   • Max δ (overdensity): {np.max(delta_nonzero):.3f}")
        print(f"   • Min δ (underdensity): {np.min(delta_nonzero):.3f}")
        
        print(f"   • Mean gradient: {np.mean(gradient_nonzero):.3f}")
        print(f"   • Max gradient: {np.max(gradient_nonzero):.3f}")

        # Identify extreme regions
        overdense_threshold = 1.0  # δ > 1 (100% above mean)
        underdense_threshold = -0.5    # δ < -0.5 (50% below mean)
        high_gradient_threshold = np.percentile(gradient_nonzero, 90)  # Top 10%

        overdense_regions = delta_map > overdense_threshold
        underdense_regions = delta_map < underdense_threshold
        high_gradient_regions = gradient_magnitude > high_gradient_threshold

        print(f"   • Overdense regions (δ > {overdense_threshold}): {np.sum(overdense_regions)} pixels")
        print(f"   • Underdense regions (δ < {underdense_threshold}): {np.sum(underdense_regions)} pixels")
        print(f"   • High gradient regions (|∇δ| > {high_gradient_threshold:.3f}): {np.sum(high_gradient_regions)} pixels")

        # Angular power spectrum analysis
        print(f"\n   📊 Calculating power spectrum...")
        try:
            cl = hp.anafast(delta_map)
            ell = np.arange(len(cl))
            print(f"      - Cℓ calculated for ℓ = 0 to {len(cl)-1}")
            print(f"      - C₂ (quadrupole): {cl[2]:.6f}")
            print(f"      - C₁₀ (dipole): {cl[10]:.6f}")
            
            # Save power spectrum
            np.savez('healpix_maps/power_spectrum.npz', ell=ell, cl=cl)
            print(f"      - ✅ Power spectrum saved: 'healpix_maps/power_spectrum.npz'")
        except Exception as e:
            print(f"      - ❌ Error in anafast: {e}")

    return delta_nonzero

if __name__ == "__main__":
    # Create maps
    result = create_high_mass_maps()
    
    if result[0] is not None:
        delta_map, gradient_magnitude, metadata, filtered_table = result
        
        # Analyze structures
        delta_vals = analyze_vorticity_structures(delta_map, gradient_magnitude, metadata)

        print(f"\n🎯 SUGGESTED NEXT STEPS:")
        print(f"   1. Detailed spectral analysis with hp.anafast()")
        print(f"   2. Calculation of the angular bispectrum of the δ field")
        print(f"   3. Non-Gaussianity analysis in high gradient regions")
        print(f"   4. Search for B-modes (vorticity) in polarization")
        print(f"   5. Comparison with ΛCDM simulations")
        print(f"   6. Study of correlation δ vs ∇δ")

        print(f"\n📁 GENERATED FILES:")
        print(f"   • high_mass_galaxies_z08-10.fits - Filtered catalog")
        print(f"   • healpix_maps/ - Directory with all HEALPix maps")
        print(f"   • healpix_maps/map_metadata.* - Metadata")

        print(f"\n✅ MAP ANALYSIS COMPLETED")
        print(f"   The maps are ready for primordial vorticity study")
    else:
        print("❌ Could not create maps")