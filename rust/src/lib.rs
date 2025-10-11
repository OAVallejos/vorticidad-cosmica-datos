
use pyo3::prelude::*;
use std::f64::consts::PI;

#[pymodule]
fn cosmic_vorticity(_py: Python, m: &PyModule) -> PyResult<()> {
    // FUNCIONES PRINCIPALES PARA EL PAPER SDSS
    m.add_function(wrap_pyfunction!(calcular_bispectro_triangular, m)?)?;
    m.add_function(wrap_pyfunction!(estadisticas_no_gaussianas, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_ratio_redshift, m)?)?;
    
    Ok(())
}

#[pyfunction]
fn calcular_bispectro_triangular(
    modos_alm: Vec<f32>,
    l_max: u16,
    configs: Vec<(u16, u16, u16)>
) -> PyResult<Vec<f32>> {
    let resultados: Vec<f32> = configs.iter()
        .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_alm, l1, l2, l3, l_max))
        .collect();
    Ok(resultados)
}

#[pyfunction]
fn calcular_ratio_redshift(
    bispectro_alto_z: Vec<f32>,
    bispectro_bajo_z: Vec<f32>
) -> PyResult<f32> {
    if bispectro_alto_z.is_empty() || bispectro_bajo_z.is_empty() {
        return Ok(0.0);
    }
    
    let norma_alto_z: f32 = bispectro_alto_z.iter().map(|x| x.abs()).sum();
    let norma_bajo_z: f32 = bispectro_bajo_z.iter().map(|x| x.abs()).sum();
    
    if norma_bajo_z > 1e-10 {
        Ok(norma_alto_z / norma_bajo_z)
    } else {
        Ok(0.0)
    }
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

fn condiciones_triangulo(l1: u16, l2: u16, l3: u16) -> bool {
    (l1 + l2 >= l3) && (l1 + l3 >= l2) && (l2 + l3 >= l1) &&
    (l1 + l2 + l3) % 2 == 0
}

fn calcular_wigner_3j(l1: u16, l2: u16, l3: u16, m1: i16, m2: i16, m3: i16) -> f32 {
    if !condiciones_triangulo(l1, l2, l3) {
        return 0.0;
    }
    if m1 + m2 + m3 != 0 {
        return 0.0;
    }
    if m1.abs() > l1 as i16 || m2.abs() > l2 as i16 || m3.abs() > l3 as i16 {
        return 0.0;
    }

    match (l1, l2, l3, m1, m2, m3) {
        (1, 1, 1, 0, 0, 0) => -0.577350269,
        (2, 2, 2, 0, 0, 0) => 0.377964473,
        (4, 4, 4, 0, 0, 0) => 0.28097694,
        (2, 2, 4, 0, 0, 0) => 0.36514837,
        (0, l_val, l_val2, 0, 0, 0) if l_val == l_val2 => {
            let signo = if l_val % 2 == 0 { 1.0 } else { -1.0 };
            signo / ((2 * l_val + 1) as f32).sqrt()
        }
        _ => {
            let signo = if (l1 + l2 + l3) % 2 == 0 { 1.0 } else { -1.0 };
            signo / ((2 * l1 + 1) as f32).sqrt()
        }
    }
}

fn obtener_modo(modos_alm: &[f32], l: u16, m: i16, _l_max: u16) -> f32 {
    let mut idx: usize = 0;
    for l_prev in 0..l {
        idx += (2 * l_prev + 1) as usize;
    }
    idx += (m + l as i16) as usize;

    if idx < modos_alm.len() { modos_alm[idx] } else { 0.0 }
}

fn calcular_bispectro_config(
    modos_alm: &[f32],
    l1: u16,
    l2: u16,
    l3: u16,
    l_max: u16
) -> f32 {
    if !condiciones_triangulo(l1, l2, l3) {
        return 0.0;
    }

    let mut suma = 0.0f32;
    let mut contador = 0u16;

    for m1 in (-(l1 as i16))..=(l1 as i16) {
        for m2 in (-(l2 as i16))..=(l2 as i16) {
            let m3 = -m1 - m2;
            if m3.abs() > l3 as i16 {
                continue;
            }

            let wigner = calcular_wigner_3j(l1, l2, l3, m1, m2, m3);
            let a1 = obtener_modo(modos_alm, l1, m1, l_max);
            let a2 = obtener_modo(modos_alm, l2, m2, l_max);
            let a3 = obtener_modo(modos_alm, l3, m3, l_max);

            if wigner != 0.0 && a1 != 0.0 && a2 != 0.0 && a3 != 0.0 {
                suma += wigner * a1 * a2 * a3;
                contador += 1;
            }
        }
    }

    if contador > 0 {
        let prefactor = ((2*l1+1) * (2*l2+1) * (2*l3+1)) as f32;
        let prefactor = (prefactor / (4.0 * PI as f32)).sqrt();
        prefactor * suma
    } else {
        0.0
    }
                   }
