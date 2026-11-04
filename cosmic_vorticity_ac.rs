use pyo3::prelude::*;
use std::f64::consts::PI;
use wigners::wigner_3j;
use rayon::prelude::*;
use std::collections::HashMap;
use std::sync::Mutex;

// =============================================================================
// MÓDULO PRINCIPAL (V19: L_MAX=25 + CACHÉ WIGNER + VALIDACIÓN ESTRICTA)
// =============================================================================
#[pymodule]
fn cosmic_vorticity(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calcular_bispectro_fkp, m)?)?;
    Ok(())
}

// =============================================================================
// TIPOS Y CONSTANTES
// =============================================================================
type Complejo = (f64, f64);

// Caché global de símbolos 3j de Wigner para evitar recálculos costosos
lazy_static::lazy_static! {
    static ref WIGNER_CACHE: Mutex<HashMap<(u32, u32, u32, i32, i32, i32), f64>> =
        Mutex::new(HashMap::new());
}

// =============================================================================
// NÚCLEO ARMÓNICO Y WIGNER 3J
// =============================================================================
fn condiciones_triangulo(l1: u16, l2: u16, l3: u16) -> bool {
    (l1 + l2 >= l3) && (l1 + l3 >= l2) && (l2 + l3 >= l1)
}

fn calcular_wigner_3j_cached(l1: u16, l2: u16, l3: u16, m1: i16, m2: i16, m3: i16) -> f64 {
    if !condiciones_triangulo(l1, l2, l3) || m1 + m2 + m3 != 0 {
        return 0.0;
    }
    if m1.abs() > l1 as i16 || m2.abs() > l2 as i16 || m3.abs() > l3 as i16 {
        return 0.0;
    }

    let key = (l1 as u32, l2 as u32, l3 as u32, m1 as i32, m2 as i32, m3 as i32);

    // Intentar leer del caché primero
    {
        let cache = WIGNER_CACHE.lock().unwrap();
        if let Some(&val) = cache.get(&key) {
            return val;
        }
    }

    // Calcular y guardar en caché
    let val = wigner_3j(l1 as u32, l2 as u32, l3 as u32, m1 as i32, m2 as i32, m3 as i32);
    {
        let mut cache = WIGNER_CACHE.lock().unwrap();
        cache.insert(key, val);
    }
    val
}

fn obtener_modo_complejo(modos_re: &[f64], modos_im: &[f64], l: u16, m: i16) -> Complejo {
    let idx: usize = (l as usize).pow(2) + (l as i16 + m) as usize;
    if idx < modos_re.len() && idx < modos_im.len() {
        (modos_re[idx], modos_im[idx])
    } else {
        (0.0, 0.0)
    }
}

fn mul_c(a: Complejo, b: Complejo) -> Complejo {
    (a.0 * b.0 - a.1 * b.1, a.0 * b.1 + a.1 * b.0)
}

fn conj_c(a: Complejo) -> Complejo {
    (a.0, -a.1)
}

fn validar_modos(modos_re: &[f64], modos_im: &[f64], l_max: u16) -> PyResult<()> {
    let tamaño_esperado = ((l_max + 1) as usize).pow(2);
    if modos_re.len() != tamaño_esperado {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("modos_re debe tener longitud {} (recibida {})", tamaño_esperado, modos_re.len())
        ));
    }
    if modos_im.len() != tamaño_esperado {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("modos_im debe tener longitud {} (recibida {})", tamaño_esperado, modos_im.len())
        ));
    }
    Ok(())
}

fn validar_configs(configs: &[(u16, u16, u16)], l_max: u16) -> PyResult<()> {
    for (i, &(l1, l2, l3)) in configs.iter().enumerate() {
        if l1 > l_max || l2 > l_max || l3 > l_max {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!(
                    "Configuración #{} ({},{},{}) excede l_max={}",
                    i, l1, l2, l3, l_max
                )
            ));
        }
        if !condiciones_triangulo(l1, l2, l3) {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!(
                    "Configuración #{} ({},{},{}) no satisface desigualdad triangular",
                    i, l1, l2, l3
                )
            ));
        }
    }
    Ok(())
}

// =============================================================================
// BISPECTRO POR CONFIGURACIÓN (núcleo matemático)
// =============================================================================
fn calcular_bispectro_config(
    modos_re: &[f64],
    modos_im: &[f64],
    l1: u16,
    l2: u16,
    l3: u16,
) -> f64 {
    if !condiciones_triangulo(l1, l2, l3) {
        return 0.0;
    }

    let mut suma_re: f64 = 0.0;

    for m1 in (-(l1 as i16))..=(l1 as i16) {
        // Acotación matemática de m2: -l2 <= m2 <= l2 y -l3 <= -m1-m2 <= l3
        let m2_min = std::cmp::max(-(l2 as i16), -m1 - (l3 as i16));
        let m2_max = std::cmp::min(l2 as i16, -m1 + (l3 as i16));

        for m2 in m2_min..=m2_max {
            let m3 = -m1 - m2;
            let wigner = calcular_wigner_3j_cached(l1, l2, l3, m1, m2, m3);
            if wigner == 0.0 {
                continue;
            }

            let a1 = obtener_modo_complejo(modos_re, modos_im, l1, m1);
            let a2 = obtener_modo_complejo(modos_re, modos_im, l2, m2);
            let a3 = obtener_modo_complejo(modos_re, modos_im, l3, m3);

            let prod_12 = mul_c(a1, a2);
            let prod_total = mul_c(prod_12, conj_c(a3));
            suma_re += wigner * prod_total.0;
        }
    }

    let prefactor = ((2.0 * l1 as f64 + 1.0)
        * (2.0 * l2 as f64 + 1.0)
        * (2.0 * l3 as f64 + 1.0))
        / (4.0 * PI);
    prefactor.sqrt() * suma_re
}

// =============================================================================
// BISPECTRO FKP (V19: SUSTRACCIÓN EMPÍRICA + L_MAX=25 + CACHÉ)
// =============================================================================
#[pyfunction]
fn calcular_bispectro_fkp(
    modos_datos_re: Vec<f64>,
    modos_datos_im: Vec<f64>,
    modos_randoms_re: Vec<f64>,
    modos_randoms_im: Vec<f64>,
    l_max: u16,
    configs: Vec<(u16, u16, u16)>,
    factor_normalizacion: f64,
    _n_bar: f64, // Parámetro preservado por compatibilidad de API, no se usa
) -> PyResult<Vec<f64>> {
    validar_modos(&modos_datos_re, &modos_datos_im, l_max)?;
    validar_modos(&modos_randoms_re, &modos_randoms_im, l_max)?;
    validar_configs(&configs, l_max)?;

    // Paralelización con Rayon sobre las configuraciones de triángulos
    let resultados: Vec<f64> = configs
        .par_iter()
        .map(|&(l1, l2, l3)| {
            let b_datos = calcular_bispectro_config(&modos_datos_re, &modos_datos_im, l1, l2, l3);
            let b_randoms =
                calcular_bispectro_config(&modos_randoms_re, &modos_randoms_im, l1, l2, l3);

            // V19: Sustracción empírica de shot noise.
            // El shot noise se cancela automáticamente al restar el bispectro de los randoms
            // (calculado con la misma ponderación FKP y la misma máscara).
            (b_datos - b_randoms) * factor_normalizacion
        })
        .collect();

    Ok(resultados)
}