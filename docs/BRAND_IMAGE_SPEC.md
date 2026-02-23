# BRAND_IMAGE_SPEC v1

## Metadata
- **style_id**: `indoor-niche-lab.v1`
- **objective**: mantener un lenguaje visual único para Home, Etapas, Pasos, Kits y Productos.

## Lenguaje visual unificado
- Realismo fotográfico con look editorial.
- Iluminación suave y natural, evitando contrastes extremos.
- Profundidad de campo moderada (sujeto claro, fondo controlado).
- Temperatura de color neutra-cálida consistente.
- Paleta base neutra (madera clara, acero, blancos, grises) con acentos orgánicos naturales.
- Encuadre limpio con espacio negativo usable para UI.
- Sin texto incrustado, sin logos, sin marcas de agua.

## Prompt backbone (header común)
Usar siempre este encabezado de estilo al inicio de cada prompt:

> Indoor Niche Lab brand style v1, editorial photorealism, soft natural light, moderate depth of field, neutral warm color temperature, clean controlled background, realistic textures, commercial composition, no visible text, no logos, no watermark.

## Negative prompts
Lista estándar a evitar en todos los slots:
- texto incrustado, subtítulos, marcas de agua, logos, branding visible.
- render 3d estilizado, cartoon, ilustración, arte digital.
- anatomía irreal, manos deformes, duplicación de objetos.
- desenfoque extremo, ruido excesivo, artefactos, sobreexposición.
- fondos caóticos, elementos ajenos a cocina/lab doméstico.

## Composición por categoría

### Home
- Escenas aspiracionales domésticas (cocina/mesada limpia).
- Planos medio y detalle con intención comercial.
- Sujetos reales o manos en acción cuando aporte contexto.

### Stage (etapa)
- Escena representativa de la fase completa.
- Contexto técnico doméstico controlado.
- Mantener continuidad visual entre cards y hero de etapa.

### Step (paso)
- Acción puntual del proceso (hidratación, pasteurización, inoculación, incubación, fructificación, cosecha, limpieza).
- Plano detalle o medio con foco en herramientas y material.
- Para pasos críticos se permiten 2 slots (`card-1`, `card-2`) para desambiguar subacciones.

### Kit
- Foto editorial del kit completo y componentes ordenados sobre superficie limpia.
- Variante de resultado con cosecha/uso final coherente con el kit.

### Product
- Producto aislado o composición de catálogo mínima.
- Fondo neutro controlado, luz suave, textura realista.
- Sin exagerar props que oculten el producto principal.

## Ratio y tamaños
- Ratio recomendado general: **3:2 horizontal**.
- Tamaños base:
  - `sm`: 640x426
  - `md`: 1024x683
  - `lg`: 1536x1024

## Política de tamaños por slot
- Home hero y banners de sección: `sm`, `md`, `lg`.
- Cards de entidad (stage/kit/product): `md`, opcional `lg`.
- Steps: `md` por defecto; `lg` opcional para detalle cuando el slot se use en hero/contexto amplio.
- No generar tamaños innecesarios: cada slot declara explícitamente los tamaños requeridos.

## Política de fallback declarada
Resolver imágenes con esta prioridad determinista:
1. `generated/<section>/<slot>/<size>.webp`
2. `generated/<section>/<slot>/<size>.png|jpg|jpeg`
3. placeholder versionado específico del slot/sección.
4. placeholder genérico global.

Fallback de tamaño recomendado: `md -> lg -> sm`.

## Convención de slot_id
- Formato: `<section>.<slot>`.
- `slot` debe ser estable en el tiempo.
- Entidades: `<type>-<slug>-<id>`.
- Steps granulares: `<step-slot>-card-1` y `<step-slot>-card-2` cuando aplique.
