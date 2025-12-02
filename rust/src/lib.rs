use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1, IntoPyArray};
use std::collections::HashMap;
use std::f64::consts::PI;
use wigners::wigner_3j;

// =============================================================================
// 0. ESTRUCTURA FINAL - MÓDULO PRINCIPAL  
// =============================================================================

#[pymodule]
fn cosmic_vorticity(py: Python, m: &PyModule) -> PyResult<()> {

    // ✅ ESTRUCTURAS COSMOLÓGICAS PARA MCMC
    m.add_class::<CosmologicalParameters>()?;
    m.add_class::<VectorFieldParameters>()?;
    m.add_class::<CosmicVorticitySystem>()?;

    // ✅ BISPECTRO Y MÉTODOS DE ANÁLISIS POR MORFOLOGÍA
    m.add_function(wrap_pyfunction!(calcular_bispectro_angular_galaxias, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_bispectro_escaleno, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_bispectro_equilatero, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_bispectro_triangular, m)?)?;

    m.add_function(wrap_pyfunction!(obtener_todas_configuraciones_triangulares, m)?)?;
    m.add_function(wrap_pyfunction!(obtener_configuraciones_por_tipo, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_bispectro_por_tipo, m)?)?;
    m.add_function(wrap_pyfunction!(analizar_morfologia_bispectro, m)?)?;

    // ✅ FUNCIONES AUXILIARES (REGISTRO)
    m.add_function(wrap_pyfunction!(estadisticas_no_gaussianas, m)?)?;
    m.add_function(wrap_pyfunction!(generar_imagen_png, m)?)?;
    m.add_function(wrap_pyfunction!(generar_reporte_html, m)?)?;
    m.add_function(wrap_pyfunction!(exportar_datos_visualizacion, m)?)?;
    m.add_function(wrap_pyfunction!(analizar_morfologia_galaxia, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_patrones_lineas, m)?)?;
    m.add_function(wrap_pyfunction!(modelo_vorticidad_plasma, m)?)?;

    // =============================================================================
    // ✅ SUBMÓDULOS ESPECIALIZADOS 
    // =============================================================================
    
    let bispectro_module = PyModule::new(py, "bispectro")?;
    bispectro_module.add_function(wrap_pyfunction!(calcular_bispectro_angular_galaxias, m)?)?;
    bispectro_module.add_function(wrap_pyfunction!(calcular_bispectro_escaleno, m)?)?;
    bispectro_module.add_function(wrap_pyfunction!(calcular_bispectro_equilatero, m)?)?;
    m.add_submodule(bispectro_module)?;

    let morfologia_module = PyModule::new(py, "morfologia")?;
    morfologia_module.add_function(wrap_pyfunction!(obtener_configuraciones_por_tipo, m)?)?;
    morfologia_module.add_function(wrap_pyfunction!(calcular_bispectro_por_tipo, m)?)?;
    morfologia_module.add_function(wrap_pyfunction!(analizar_morfologia_bispectro, m)?)?;
    m.add_submodule(morfologia_module)?;

    let utilidades_module = PyModule::new(py, "utilidades")?;
    utilidades_module.add_function(wrap_pyfunction!(estadisticas_no_gaussianas, m)?)?;
    utilidades_module.add_function(wrap_pyfunction!(generar_imagen_png, m)?)?;
    utilidades_module.add_function(wrap_pyfunction!(exportar_datos_visualizacion, m)?)?;
    m.add_submodule(utilidades_module)?;

    Ok(())
}

// =============================================================================
// 1. ESTRUCTURAS COSMOLÓGICAS (MCMC)
// =============================================================================

#[pyclass]
#[derive(Clone)]
struct CosmologicalParameters {
    #[pyo3(get)]
    h0: f64,
    #[pyo3(get)]
    omega_m: f64,
    #[pyo3(get)]
    omega_b: f64,
    #[pyo3(get)]
    omega_r: f64,
    #[pyo3(get)]
    omega_lambda: f64,
    #[pyo3(get)]
    sigma_8: f64,
    #[pyo3(get)]
    n_s: f64,
    #[pyo3(get)]
    tau: f64,
}

#[pymethods]
impl CosmologicalParameters {
    #[new]
    fn new(
        h0: f64,
        omega_m: f64,
        omega_b: f64,
        omega_r: f64,
        omega_lambda: f64,
        sigma_8: f64,
        n_s: f64,
        tau: f64
    ) -> Self {
        Self {
            h0,
            omega_m,
            omega_b,
            omega_r,
            omega_lambda,
            sigma_8,
            n_s,
            tau,
        }
    }
}

#[pyclass]
#[derive(Clone)]
struct VectorFieldParameters {
    #[pyo3(get)]
    alpha: f64,
    #[pyo3(get)]
    m_a: f64,
    #[pyo3(get)]
    lambda_a: f64,
    #[pyo3(get)]
    beta: f64,
    #[pyo3(get)]
    gamma_2: f64,
    #[pyo3(get)]
    v: f64,
    #[pyo3(get)]
    m_phi: f64,
}

#[pymethods]
impl VectorFieldParameters {
    #[new]
    fn new(
        alpha: f64,
        m_a: f64,
        lambda_a: f64,
        beta: f64,
        gamma_2: f64,
        v: f64,
        m_phi: f64
    ) -> Self {
        Self {
            alpha,
            m_a,
            lambda_a,
            beta,
            gamma_2,
            v,
            m_phi,
        }
    }
}

#[pyclass]
struct CosmicVorticitySystem {
    #[pyo3(get)]
    cosmo_params: CosmologicalParameters,
    #[pyo3(get)]
    vector_params: VectorFieldParameters,
    #[pyo3(get)]
    initial_redshift: f64,
}

// =============================================================================
// 2. BISPECTRO ANGULAR (NÚCLEO)
// =============================================================================

fn condiciones_triangulo(l1: u16, l2: u16, l3: u16) -> bool {
    (l1 + l2 >= l3) && (l1 + l3 >= l2) && (l2 + l3 >= l1) &&
    (l1 + l2 + l3) % 2 == 0
}

fn calcular_wigner_3j(l1: u16, l2: u16, l3: u16, m1: i16, m2: i16, m3: i16) -> f32 {
    if !condiciones_triangulo(l1, l2, l3) || m1 + m2 + m3 != 0 {
        return 0.0;
    }
    if m1.abs() > l1 as i16 || m2.abs() > l2 as i16 || m3.abs() > l3 as i16 {
        return 0.0;
    }

    wigner_3j(
        l1 as u32, l2 as u32, l3 as u32,
        m1 as i32, m2 as i32, m3 as i32
    ) as f32
}

fn obtener_modo(modos_b: &[f32], l: u16, m: i16, _l_max: u16) -> f32 {
    let idx: usize = (l as usize).pow(2) + (m + l as i16) as usize;

    if idx < modos_b.len() {
        modos_b[idx]
    } else {
        0.0
    }
}

fn calcular_bispectro_config(
    modos_b: &[f32],
    l1: u16,
    l2: u16,
    l3: u16,
    l_max: u16
) -> f32 {
    if !condiciones_triangulo(l1, l2, l3) {
        return 0.0;
    }

    let mut suma = 0.0f32;

    for m1 in (-(l1 as i16))..=(l1 as i16) {
        for m2 in (-(l2 as i16))..=(l2 as i16) {
            let m3 = -m1 - m2;
            if m3.abs() > l3 as i16 {
                continue;
            }

            let wigner = calcular_wigner_3j(l1, l2, l3, m1, m2, m3);
            if wigner == 0.0 {
                continue;
            }

            let a1 = obtener_modo(modos_b, l1, m1, l_max);
            let a2 = obtener_modo(modos_b, l2, m2, l_max);

            // ✅ CORRECCIÓN CRÍTICA: Conjugación para campo real
            let a3_m_negativo = obtener_modo(modos_b, l3, -m3, l_max);
            let factor_paridad = if m3 % 2 == 0 { 1.0 } else { -1.0 };
            let a3_conj = a3_m_negativo * factor_paridad;

            suma += wigner * a1 * a2 * a3_conj;
        }
    }

    if suma.abs() > 1e-15 {
        let prefactor = ((2*l1+1) as f64 * (2*l2+1) as f64 * (2*l3+1) as f64) / (4.0 * PI);
        (prefactor.sqrt() as f32) * suma
    } else {
        0.0
    }
}

#[pyfunction]
fn calcular_bispectro_angular_galaxias(
    modos_b: Vec<f32>,
    l_max: u16,
    configs: Vec<(u16, u16, u16)>
) -> PyResult<Vec<f32>> {
    let resultados: Vec<f32> = configs.iter()
        .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_b, l1, l2, l3, l_max))
        .collect();
    Ok(resultados)
}

fn obtener_configuraciones_escaleno() -> Vec<(u16, u16, u16)> {
    vec![
        (2, 2, 2), (4, 4, 4),
        (2, 3, 4), (2, 4, 5),
        (3, 4, 6), (2, 5, 6),
        (3, 5, 7), (4, 5, 8),
    ]
}

#[pyfunction]
fn calcular_bispectro_escaleno(
    modos_b: Vec<f32>,
    l_max: u16
) -> PyResult<Vec<f32>> {
    let configs = obtener_configuraciones_escaleno();
    let resultados: Vec<f32> = configs.iter()
        .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_b, l1, l2, l3, l_max))
        .collect();
    Ok(resultados)
}

#[pyfunction]
fn calcular_bispectro_equilatero(
    modos_b: Vec<f32>,
    l_max: u16
) -> PyResult<Vec<f32>> {
    let configs = vec![(2, 2, 2), (4, 4, 4)];
    let resultados: Vec<f32> = configs.iter()
        .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_b, l1, l2, l3, l_max))
        .collect();
    Ok(resultados)
}

// =============================================================================
// 2.5. MORFOLOGÍA DE BISPECTRO (NUEVAS FUNCIONES)
// =============================================================================

fn obtener_configuraciones_triangulares_completas() -> Vec<(u16, u16, u16)> {
    // Definición completa de configuraciones (equilatero, isosceles, escaleno, etc.)
    vec![
        (2, 2, 2), (4, 4, 4), (6, 6, 6), (8, 8, 8), (10, 10, 10), // Equiláteros
        (2, 2, 4), (4, 4, 8), (6, 6, 12), (8, 8, 16), // Isósceles (simétricos)
        (2, 4, 2), (4, 8, 4), (6, 12, 6), // Isósceles (alternos)
        (4, 2, 2), (8, 4, 4), (12, 6, 6), // Isósceles (alternos 2)
        (2, 3, 4), (3, 4, 5), (4, 5, 6), (5, 6, 7), (6, 7, 8), (7, 8, 9), (8, 9, 10), // Escalenos suaves
        (2, 4, 5), (3, 5, 7), (4, 6, 9), (5, 8, 11), (6, 10, 13), // Escalenos con saltos
        (2, 5, 6), (3, 7, 8), (4, 9, 10), (5, 11, 12), // Escalenos asimétricos
        (2, 3, 5), (3, 4, 7), (4, 5, 9), (5, 6, 11), // Casi degenerados (Aplastados)
        (8, 1, 7), (10, 3, 7), // Aplastados extremos
        (1, 8, 9), (2, 10, 12), (1, 10, 11), // Alargados
        (1, 1, 2), (50, 50, 50), (100, 100, 100), // Referencia
    ]
}

#[pyfunction]
fn obtener_todas_configuraciones_triangulares() -> PyResult<Vec<(u16, u16, u16)>> {
    Ok(obtener_configuraciones_triangulares_completas())
}

#[pyfunction]
fn obtener_configuraciones_por_tipo(tipo: &str) -> PyResult<Vec<(u16, u16, u16)>> {
    let todas = obtener_configuraciones_triangulares_completas();

    let filtradas: Vec<(u16, u16, u16)> = todas.into_iter()
        .filter(|&(l1, l2, l3)| {
            if !condiciones_triangulo(l1, l2, l3) {
                return false;
            }

            let mut sorted = [l1, l2, l3];
            sorted.sort();
            let [s1, s2, s3] = sorted;

            match tipo {
                "equilatero" => l1 == l2 && l2 == l3,
                "isosceles" => (l1 == l2 && l2 != l3) ||
                              (l1 == l3 && l3 != l2) ||
                              (l2 == l3 && l3 != l1),
                "escaleno" => l1 != l2 && l2 != l3 && l1 != l3,
                "aplastado" => s1 + s2 >= s3 - 1 && s1 + s2 <= s3 + 1,
                "alargado" => s3 >= 3 * s1 && s1 > 0,
                _ => true // Todas las configuraciones
            }
        })
        .collect();

    Ok(filtradas)
}

fn calcular_estadisticas_triangulo(valores: &[f32], _tipo: &str) -> Vec<f32> {
    if valores.is_empty() {
        return vec![0.0, 0.0, 0.0, 0.0];
    }

    let n = valores.len() as f32;
    let suma: f32 = valores.iter().sum();
    let promedio = suma / n;

    let varianza: f32 = valores.iter()
        .map(|&x| (x - promedio).powi(2))
        .sum::<f32>() / n;

    let maximo = valores.iter().fold(f32::NEG_INFINITY, |a, &b| a.max(b));
    let minimo = valores.iter().fold(f32::INFINITY, |a, &b| a.min(b));

    vec![promedio, varianza, maximo, minimo]
}

#[pyfunction]
fn calcular_bispectro_por_tipo(
    modos_b: Vec<f32>,
    l_max: u16,
    tipo_triangulo: &str
) -> PyResult<HashMap<String, Vec<f32>>> {
    let configs = obtener_configuraciones_por_tipo(tipo_triangulo)?;

    let mut resultados = HashMap::new();

    let valores: Vec<f32> = configs.iter()
        .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_b, l1, l2, l3, l_max))
        .collect();

    resultados.insert("valores".to_string(), valores.clone());
    resultados.insert("configuraciones".to_string(),
        configs.iter().map(|&(l1, l2, l3)| (l1 + l2 + l3) as f32).collect());

    let stats = calcular_estadisticas_triangulo(&valores, tipo_triangulo);
    resultados.insert("estadisticas".to_string(), stats);

    Ok(resultados)
}

#[pyfunction]
fn analizar_morfologia_bispectro(
    modos_b: Vec<f32>,
    l_max: u16
) -> PyResult<HashMap<String, f32>> {
    let tipos = ["equilatero", "isosceles", "escaleno", "aplastado", "alargado"];
    let mut resultados = HashMap::new();

    for tipo in tipos.iter() {
        let configs = obtener_configuraciones_por_tipo(tipo)?;
        let valores: Vec<f32> = configs.iter()
            .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_b, l1, l2, l3, l_max))
            .collect();

        if !valores.is_empty() {
            let promedio: f32 = valores.iter().sum::<f32>() / valores.len() as f32;
            resultados.insert(tipo.to_string(), promedio);
        } else {
            resultados.insert(tipo.to_string(), 0.0);
        }
    }

    let equilatero = *resultados.get("equilatero").unwrap_or(&0.0);
    let escaleno = *resultados.get("escaleno").unwrap_or(&0.0);
    let aplastado = *resultados.get("aplastado").unwrap_or(&0.0);

    if equilatero.abs() > 1e-10 {
        resultados.insert("ratio_escaleno_equilatero".to_string(), escaleno / equilatero);
        resultados.insert("ratio_aplastado_equilatero".to_string(), aplastado / equilatero);
    } else {
        resultados.insert("ratio_escaleno_equilatero".to_string(), 0.0);
        resultados.insert("ratio_aplastado_equilatero".to_string(), 0.0);
    }

    Ok(resultados)
}

// =============================================================================
// 3. SISTEMA COSMOLÓGICO COMPLETO (MCMC)
// =============================================================================

#[pymethods]
impl CosmicVorticitySystem {
    #[new]
    fn new(
        cosmo_params: CosmologicalParameters,
        vector_params: VectorFieldParameters,
        initial_redshift: f64
    ) -> Self {
        Self {
            cosmo_params,
            vector_params,
            initial_redshift,
        }
    }

    fn integrate_to_redshift(&self, target_z: f64, initial_state: Vec<f64>) -> PyResult<HashMap<String, Vec<f64>>> {
        let mut state = initial_state;
        let mut z = self.initial_redshift;
        let dz = -0.01;

        if self.vector_params.alpha <= 0.0 || self.vector_params.m_a <= 0.0 || self.vector_params.beta <= 0.0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Parámetros vectoriales no positivos."
            ));
        }

        let mut results = HashMap::new();
        let mut z_values = Vec::new();
        let mut a0_values = Vec::new();
        let mut phi_values = Vec::new();
        let mut rho_b_values = Vec::new();
        let mut hubble_values = Vec::new();

        while z > target_z {
            state = self.rk4_step(z, &state, dz);
            z += dz;

            if state[0].is_nan() || !state[0].is_finite() || state[0] < 1e-10 || z < -0.1 {
                return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "Integración numérica divergió"
                ));
            }

            z_values.push(z);
            a0_values.push(state[0]);
            phi_values.push(state[2]);
            rho_b_values.push(state[4]);
            hubble_values.push(self.hubble_parameter(z, &state));
        }

        results.insert("redshift".to_string(), z_values);
        results.insert("a0".to_string(), a0_values);
        results.insert("phi".to_string(), phi_values);
        results.insert("rho_b".to_string(), rho_b_values);
        results.insert("hubble".to_string(), hubble_values);

        Ok(results)
    }

    fn calculate_bispectrum_evolution(&self, integration_results: HashMap<String, Vec<f64>>) -> PyResult<Vec<f64>> {
        let a0_values = integration_results.get("a0").unwrap();
        let redshift_values = integration_results.get("redshift").unwrap();

        let mut bispectrum = Vec::new();

        for (i, &a0) in a0_values.iter().enumerate() {
            let z = redshift_values[i];

            if a0.is_nan() || !a0.is_finite() {
                 return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "NaN/Infinito en A0 durante el cálculo del bispectro"
                ));
            }
            let b = self.vector_params.alpha * a0.powi(2) * (1.0 + z).powf(-0.4);
            bispectrum.push(b);
        }

        Ok(bispectrum)
    }

    fn calculate_log_likelihood(&self,
                               data_obs_sdss: (f64, f64),
                               data_obs_desi: (f64, f64)) -> PyResult<f64> {

        let _a_omega = self.vector_params.alpha * 2.0;

        let log_beta = self.vector_params.beta.abs().log10();
        let n_omega = -0.4_f64 + 0.01 * (log_beta + 40.0);

        let z_ref_sdss = 0.15_f64;
        let z_high_sdss = 0.75_f64;
        let z_ref_desi = 0.5_f64;
        let z_high_desi = 0.9_f64;

        // EVOLUCIÓN (High-z / Low-z)
        let evolution_sdss = (1.0 + z_high_sdss).powf(n_omega) / (1.0 + z_ref_sdss).powf(n_omega);

        // EVOLUCIÓN (Low-z / High-z)
        let evolution_desi = (1.0 + z_ref_desi).powf(n_omega) / (1.0 + z_high_desi).powf(n_omega);

        let evolution_sdss = evolution_sdss.clamp(0.1, 20.0);
        let evolution_desi = evolution_desi.clamp(0.1, 20.0);

        let (obs_sdss, err_sdss) = data_obs_sdss;
        let (obs_desi, err_desi) = data_obs_desi;

        let chi2_sdss = (evolution_sdss - obs_sdss).powi(2) / err_sdss.powi(2);
        let chi2_desi = (evolution_desi - obs_desi).powi(2) / err_desi.powi(2);
        let chi2_total = chi2_sdss + chi2_desi;

        let ln_likelihood = -0.5 * chi2_total;

        Ok(ln_likelihood)
    }

    fn calculate_log_likelihood_debug(
        &self,
        data_obs_sdss: (f64, f64),
        data_obs_desi: (f64, f64),
    ) -> PyResult<(f64, String)> {

        const EXTREME_PENALTY: f64 = -1.0e30;

        let _a_omega = self.vector_params.alpha * 2.0;

        let log_beta = self.vector_params.beta.abs().log10();
        let n_omega = -0.4_f64 + 0.01 * (log_beta + 40.0);

        let z_ref_sdss = 0.15_f64;
        let z_high_sdss = 0.75_f64;
        let z_ref_desi = 0.5_f64;
        let z_high_desi = 0.9_f64;

        let evolution_sdss = (1.0 + z_high_sdss).powf(n_omega) / (1.0 + z_ref_sdss).powf(n_omega);
        let evolution_desi = (1.0 + z_ref_desi).powf(n_omega) / (1.0 + z_high_desi).powf(n_omega);

        let evolution_sdss = evolution_sdss.clamp(0.1, 20.0);
        let evolution_desi = evolution_desi.clamp(0.1, 20.0);

        let (obs_sdss, err_sdss) = data_obs_sdss;
        let (obs_desi, err_desi) = data_obs_desi;

        if err_sdss.abs() < 1e-10 || err_desi.abs() < 1e-10 {
            return Ok((EXTREME_PENALTY, "Error de datos cero".to_string()));
        }

        let chi2_sdss = (evolution_sdss - obs_sdss).powi(2) / err_sdss.powi(2);
        let chi2_desi = (evolution_desi - obs_desi).powi(2) / err_desi.powi(2);
        let chi2_total = chi2_sdss + chi2_desi;

        let log_likelihood = -0.5 * chi2_total;

        if log_likelihood.is_nan() || !log_likelihood.is_finite() {
            return Ok((-1.0e10, "Likelihood final NaN/Inf".to_string()));
        }

        let debug_info = format!(
            "evolution_sdss={:.2}, evolution_desi={:.2}, n_omega={:.3}, chi2_total={:.2}",
            evolution_sdss, evolution_desi, n_omega, chi2_total
        );

        Ok((log_likelihood, debug_info))
    }

    fn calculate_log_likelihood_simple(
        &self,
        data_obs_sdss: (f64, f64),
        data_obs_desi: (f64, f64),
    ) -> PyResult<f64> {
        match self.calculate_log_likelihood_debug(data_obs_sdss, data_obs_desi) {
            Ok((lnl, _)) => Ok(lnl),
            Err(e) => Err(e),
        }
    }
}

// Implementaciones internas (hubble_parameter, coupled_system, rk4_step, etc.)
impl CosmicVorticitySystem {

    fn hubble_parameter(&self, z: f64, state: &[f64]) -> f64 {
        let h0 = self.cosmo_params.h0;
        let omega_m = self.cosmo_params.omega_m;
        let omega_r = self.cosmo_params.omega_r;
        let omega_lambda = self.cosmo_params.omega_lambda;

        let standard = omega_m * (1.0 + z).powi(3)
                     + omega_r * (1.0 + z).powi(4)
                     + omega_lambda;

        let a0 = state[0];
        let omega_a = self.calculate_omega_a(z, a0);

        h0 * (standard + omega_a).abs().sqrt()
    }

    fn coupled_system(&self, z: f64, state: &[f64]) -> Vec<f64> {
        let mut derivatives = vec![0.0; 6];

        if state.len() < 6 { return derivatives; }

        let a0 = state[0];
        let da0_dz = state[1];
        let phi = state[2];
        let rho_b = state[4];
        let rho_r = state[5];

        let hz = self.hubble_parameter(z, state);
        let h0 = self.cosmo_params.h0;
        let e_z = hz / h0;

        derivatives[0] = state[1];
        derivatives[1] = self.equation_a0(z, a0, da0_dz, phi, rho_b, e_z);
        derivatives[2] = state[3];
        derivatives[3] = self.equation_phi(z, phi, state[3], a0, e_z);
        derivatives[4] = self.equation_rho_b(z, rho_b, a0, e_z);
        derivatives[5] = -4.0 * rho_r / (1.0 + z);

        derivatives
    }

    fn rk4_step(&self, z: f64, state: &[f64], dz: f64) -> Vec<f64> {
        let k1 = self.coupled_system(z, state);
        let state_k2: Vec<f64> = state.iter().zip(&k1).map(|(&s, &k)| s + k * dz * 0.5).collect();
        let k2 = self.coupled_system(z + dz * 0.5, &state_k2);
        let state_k3: Vec<f64> = state.iter().zip(&k2).map(|(&s, &k)| s + k * dz * 0.5).collect();
        let k3 = self.coupled_system(z + dz * 0.5, &state_k3);
        let state_k4: Vec<f64> = state.iter().zip(&k3).map(|(&s, &k)| s + k * dz).collect();
        let k4 = self.coupled_system(z + dz, &state_k4);

        state.iter()
            .zip(&k1).zip(&k2).zip(&k3).zip(&k4)
            .map(|((((&s, &k1), &k2), &k3), &k4)| {
                s + (k1 + 2.0*k2 + 2.0*k3 + k4) * dz / 6.0
            })
            .collect()
    }

    fn calculate_omega_a(&self, z: f64, a0: f64) -> f64 {
        let rho_crit_0 = 8.0e-11;

        let kinetic_energy = 0.5 * self.vector_params.m_a.powi(2) * a0.powi(2);
        let potential_energy = 0.25 * self.vector_params.alpha * (a0.powi(2) - self.vector_params.v.powi(2)).powi(2);
        let rho_a = (kinetic_energy + potential_energy) * (1.0 + z).powf(3.0);

        rho_a / rho_crit_0
    }

    fn equation_a0(&self, z: f64, a0: f64, da0_dz: f64, phi: f64, rho_b: f64, e_z: f64) -> f64 {
        let hubble_term = (4.0 / (1.0 + z)) * da0_dz;
        let mass_term = self.vector_params.m_a.powi(2) * a0 / (e_z.powi(2) * (1.0 + z).powi(2));
        let coupling_term = 2.0 * self.vector_params.alpha * phi * a0 * (a0.powi(2) - self.vector_params.v.powi(2));
        let matter_term = (self.vector_params.beta * rho_b) / (e_z.powi(2) * (1.0 + z).powi(2));

        -hubble_term - mass_term - coupling_term + matter_term
    }

    fn equation_phi(&self, z: f64, phi: f64, dphi_dz: f64, a0: f64, e_z: f64) -> f64 {
        let hubble_term = (4.0 / (1.0 + z)) * dphi_dz;
        let mass_term = self.vector_params.m_phi.powi(2) * phi / (e_z.powi(2) * (1.0 + z).powi(2));
        let source_term = self.vector_params.alpha * (a0.powi(2) - self.vector_params.v.powi(2)).powi(2) /
                         (e_z.powi(2) * (1.0 + z).powi(2));

        -hubble_term - mass_term + source_term
    }

    fn equation_rho_b(&self, z: f64, rho_b: f64, a0: f64, e_z: f64) -> f64 {
        let expansion_term = 3.0 * rho_b / (1.0 + z);
        let exchange_term = self.vector_params.beta * a0 * rho_b / (e_z * (1.0 + z));

        expansion_term - exchange_term
    }

    fn estimate_halo_mass(&self, stellar_mass: f64) -> f64 {
        stellar_mass * 100.0
    }

    fn calculate_gw_delay(&self, z: f64, above_threshold: bool) -> f64 {
        if above_threshold {
            1.7 * (1.0 + z).powf(1.6)
        } else {
            1.7
        }
    }
}

// =============================================================================
// 4. FUNCIONES AUXILIARES (SIN DUPLICADOS)
// =============================================================================

#[pyfunction]
fn calcular_bispectro_triangular(
    modos_b: Vec<f32>,
    l_max: u16,
    configs: Vec<(u16, u16, u16)>
) -> PyResult<Vec<f32>> {
    calcular_bispectro_angular_galaxias(modos_b, l_max, configs)
}

#[pyfunction]
fn modelo_vorticidad_plasma(
    parametros: Vec<f32>,
    n_puntos: u16
) -> PyResult<Vec<f32>> {
    let resultado: Vec<f32> = (0..n_puntos).map(|i| {
        let x = i as f32 / n_puntos as f32 * 2.0 * PI as f32;
        parametros[0] * x.sin() * (-parametros[1] * x).exp()
    }).collect();
    Ok(resultado)
}

#[pyfunction]
fn estadisticas_no_gaussianas(datos: Vec<f32>) -> PyResult<Vec<f32>> {
    let n = datos.len() as f32;
    let media = datos.iter().sum::<f32>() / n;
    let varianza = datos.iter().map(|&x| (x - media).powi(2)).sum::<f32>() / n;
    let desviacion = varianza.sqrt();

    let asimetria = if desviacion > 0.0 {
        datos.iter().map(|&x| ((x - media) / desviacion).powi(3)).sum::<f32>() / n
    } else {
        0.0
    };

    let curtosis = if desviacion > 0.0 {
        datos.iter().map(|&x| ((x - media) / desviacion).powi(4)).sum::<f32>() / n - 3.0
    } else {
        0.0
    };

    Ok(vec![media, varianza, asimetria, curtosis])
}

// Funciones de utilidad para visualización
#[pyfunction]
fn generar_imagen_png(
    _datos: Vec<f32>,
    dimensiones: (u32, u32),
    nombre_archivo: String
) -> PyResult<()> {
    use std::fs::File;
    use std::io::BufWriter;
    let (_ancho, _alto) = dimensiones;
    let mut buffer = Vec::new();
    buffer.extend_from_slice(b"PLACEHOLDER PNG DATA");
    let file = File::create(nombre_archivo)?;
    let mut writer = BufWriter::new(file);
    std::io::Write::write_all(&mut writer, &buffer)?;
    Ok(())
}

#[pyfunction]
fn generar_reporte_html(
    _resultados: Vec<f32>,
    _mapa_intensidad: Vec<f32>,
    _dimensiones: (u32, u32),
    nombre_archivo: String
) -> PyResult<()> {
    use std::fs::File;
    use std::io::Write;
    let mut file = File::create(nombre_archivo)?;
    file.write_all(b"<html><body>Reporte HTML de prueba</body></html>")?;
    Ok(())
}

#[pyfunction]
fn exportar_datos_visualizacion(
    _mapa_intensidad: Vec<f32>,
    _mapa_ratio: Vec<f32>,
    dimensiones: (u32, u32),
    _resultados: Vec<f32>
) -> PyResult<String> {
    let json_data = format!(r#"{{
        "dimensiones": [{}, {}],
        "mapa_intensidad": "datos_redactados",
        "mapa_ratio": "datos_redactados",
        "metricas_vorticidad": [],
        "ratio_promedio": 0.0,
        "conclusion": "SIN_EVIDENCIA_FUERTE"
    }}"#,
        dimensiones.0, dimensiones.1
    );

    Ok(json_data)
}

fn calcular_patron_rotacional(_mapa: &[f32], _dimensiones: (u32, u32)) -> f32 {
    0.1 // Placeholder
}

#[pyfunction]
fn analizar_morfologia_galaxia(
    mapa_intensidad: Vec<f32>,
    dimensiones: (u32, u32),
    umbral_snr: f32
) -> PyResult<Vec<f32>> {
    let (ancho, alto) = dimensiones;
    let mut resultados = Vec::new();

    // CORRECCIÓN: Definir suma_total que faltaba
    let suma_total: f32 = mapa_intensidad.iter()
        .map(|&x| if x > umbral_snr { x } else { 0.0 })
        .sum();

    if suma_total > 0.0 {
        resultados.push(ancho as f32 / 2.0);
        resultados.push(alto as f32 / 2.0);
        resultados.push(0.5); // Elipticidad (Placeholder)
        resultados.push(calcular_patron_rotacional(&mapa_intensidad, dimensiones));
    } else {
        resultados.push(0.0);
        resultados.push(0.0);
        resultados.push(0.0);
        resultados.push(0.0);
    }

    Ok(resultados)
}

#[pyfunction]
fn calcular_patrones_lineas(
    mapa_oiii: Vec<f32>,
    mapa_cii: Vec<f32>,
    dimensiones: (u32, u32)
) -> PyResult<Vec<f32>> {
    let (ancho, alto) = dimensiones;
    let mut resultados = Vec::new();

    let mut mapa_ratio = Vec::new();
    let mut ratios_validos = Vec::new();

    for i in 0..mapa_oiii.len() {
        if i < mapa_cii.len() && mapa_cii[i] > 0.0 {
            let ratio = mapa_oiii[i] / mapa_cii[i];
            mapa_ratio.push(ratio);
            if ratio.is_finite() {
                ratios_validos.push(ratio);
            }
        } else {
            mapa_ratio.push(0.0);
        }
    }

    // Bispectro adaptado (Placeholder simple)
    let configs = vec![(2, 2, 2), (3, 3, 3), (2, 3, 4)];
    let bispectro_resultados: Vec<f32> = configs.iter().map(|&(l1, l2, l3)| (l1 + l2 + l3) as f32 * 0.1 ).collect();

    resultados.extend(bispectro_resultados);

    if !ratios_validos.is_empty() {
        let ratio_promedio: f32 = ratios_validos.iter().sum::<f32>() / ratios_validos.len() as f32;
        resultados.push(ratio_promedio);

        let ratio_max = ratios_validos.iter().fold(0.0f32, |a, &b| a.max(b));
        resultados.push(ratio_max);
    }

    Ok(resultados)
}