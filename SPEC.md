# Especificación Congelada del Bispectro Angular
Versión: 19 (Alineada con kernel AC V19/V20)  
Fecha de congelamiento: 2026-11-01  
Estado: ✅ VERIFICADO con tests analíticos  
Kernel: `cosmic_vorticity_ac.rs`

---

## 1. Definición Matemática Implementada

El kernel calcula el bispectro angular real (parte real) con el prefactor de Gaunt completo:

$$ B_{l_1 l_2 l_3} = \sqrt{\frac{(2l_1+1)(2l_2+1)(2l_3+1)}{4\pi}} \sum_{m_1, m_2, m_3} \begin{pmatrix} l_1 & l_2 & l_3 \\ m_1 & m_2 & m_3 \end{pmatrix} \text{Re}(a_{l_1 m_1} \cdot a_{l_2 m_2} \cdot a^_{l_3 m_3}) $$

Donde:
- $a_{lm}$ son los coeficientes armónicos esféricos complejos representados como tuplas `(Re, Im)` de `f64`.
- $\begin{pmatrix} l_1 & l_2 & l_3 \\ m_1 & m_2 & m_3 \end{pmatrix}$ es el símbolo de Wigner 3j (fase Condon-Shortley).
- $a^_{l_3 m_3}$ es el conjugado complejo del tercer modo.
- La suma está restringida por $m_1 + m_2 + m_3 = 0$ (regla de selección del Wigner 3j).
- El kernel devuelve solo $\text{Re}(B)$ porque la parte imaginaria se cancela bajo simetría esférica en campos reales.

---

## 2. Layout de Memoria (Array Denso)

Los modos armónicos se almacenan en vectores 1D densos de `f64` (doble precisión en todo el pipeline).  
El tamaño total del array para un $l_{max}$ dado es:  
$$ N_{KERNEL} = (l_{max} + 1)^2 $$

La función de mapeo de índices $(l, m) \rightarrow \text{idx}$ es:
$$ \text{idx}(l, m) = l^2 + l + m $$

Ejemplos de validación:
- $l=0, m=0 \rightarrow 0$
- $l=1, m=-1 \rightarrow 1$
- $l=2, m=2 \rightarrow 8$
- $l=3, m=0 \rightarrow 12$

---

## 3. Firma Real del Kernel (PyO3)

### 3.1. Función Exportada (API Pública)
Este módulo expone únicamente la siguiente función al entorno Python:

```rust
#[pyfunction]
fn calcular_bispectro_fkp(
    modos_datos_re: Vec<f64>, 
    modos_datos_im: Vec<f64>, 
    modos_randoms_re: Vec<f64>, 
    modos_randoms_im: Vec<f64>, 
    l_max: u16, 
    configs: Vec<(u16, u16, u16)>, 
    factor_normalizacion: f64, 
    _n_bar: f64, // Preservado por compatibilidad de API, no se usa internamente
) -> PyResult<Vec<f64>>
```
Fórmula aplicada: `(B_datos - B_randoms)  factor_normalizacion`

### 3.2. Funciones Internas (No exportadas a Python)
El código incluye helpers privados para mantener la modularidad y el rendimiento:
- `calcular_bispectro_config`: Núcleo matemático que evalúa la suma para una tripla $(l_1, l_2, l_3)$ específica.
- `calcular_wigner_3j_cached`: Envoltorio con caché global para los símbolos de Wigner.
- `validar_modos`: Verifica que los vectores de entrada tengan la longitud exacta $(l_{max} + 1)^2$.
- `validar_configs`: Verifica que todas las configuraciones respeten $l \le l_{max}$ y la desigualdad triangular.
- `obtener_modo_complejo`, `mul_c`, `conj_c`: Utilidades de aritmética compleja en `f64`.

> Nota: Las funciones de vorticidad 3D y morfología de triángulos mencionadas en versiones anteriores no están presentes en este archivo V19. Este módulo se centra exclusivamente en el cálculo del bispectro armónico FKP.

---

## 4. Reglas de Validación y Condiciones de Triángulo

Para que una tripla $(l_1, l_2, l_3)$ y $(m_1, m_2, m_3)$ sea válida, el kernel aplica estrictamente:

1. Desigualdad triangular:  
   $l_1 + l_2 \ge l_3 \quad \land \quad l_1 + l_3 \ge l_2 \quad \land \quad l_2 + l_3 \ge l_1$
2. Conservación de momento angular ($m$):  
   $m_1 + m_2 + m_3 = 0$
3. Límites de $m$:  
   $|m_1| \le l_1 \quad \land \quad |m_2| \le l_2 \quad \land \quad |m_3| \le l_3$
4. Validación de tamaño de array:  
   `modos_re.len() == (l_max + 1)^2` y `modos_im.len() == (l_max + 1)^2`. Si no coincide, lanza `PyValueError`.

---

## 5. Notas de Rendimiento y Precisión (V19)

- Precisión nativa `f64`: Todo el pipeline (entrada, aritmética compleja, caché de Wigner y salida) utiliza exclusivamente `f64`. No hay conversión desde `f32` ni promoción temporal.
- Caché de Wigner 3j: Se utiliza una estructura global `WIGNER_CACHE` (`lazy_static` + `Mutex<HashMap>`) para evitar el recálculo costoso de símbolos de Wigner idénticos durante la iteración.
- Paralelización: La evaluación sobre el vector `configs` utiliza `rayon::prelude::` (`.par_iter()`) para distribuir la carga de trabajo de forma eficiente entre múltiples hilos.
- Límite superior: El módulo está optimizado y validado hasta $l_{max} = 25$ (según comentarios del código V19).

---

## 6. Historial de Verificación (V19)

| Test | Descripción | Estado |
|------|-------------|--------|
| `layout` | Validación de mapeo $l^2 + l + m$ con `f64` | ✅ PASS |
| `validacion_estricta` | Rechazo de configs que violan desigualdad triangular o límites de $m$ | ✅ PASS |
| `wigner_cache` | Verificación de hit/miss en `WIGNER_CACHE` y corrección del valor | ✅ PASS |
| `fkp_sustraccion` | Cálculo correcto de $(B_{datos} - B_{randoms}) \times factor$ | ✅ PASS |
| `paralelismo` | Ejecución concurrente sin condiciones de carrera en la caché | ✅ PASS |
| `complejidad_lmax25` | Estabilidad de memoria y tiempo de ejecución para $l_{max}=25$ | ✅ PASS |
```