# indoor-niche-lab

PROYECTO: Indoor Niche Lab — sitio tutorial + base de datos de contenidos + monetización por venta de insumos (indoor).

## Requisitos
- Python 3.10+

## Setup rápido
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Inicializar base de datos
```bash
python scripts/init_db.py
python scripts/seed_demo.py
```

## Generar tutorial demo adicional
```bash
python scripts/generate_tutorials.py
```

## Correr servidor
```bash
./uvicorn.sh
```

o

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Ejecutar tests
```bash
pytest -q
```
