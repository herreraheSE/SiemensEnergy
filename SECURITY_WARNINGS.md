# ChatDev - Guía de Configuración Segura

## ⚠️ Warnings Detectados y Cómo Solucionarlos

### 1. Python Deprecation Warning: `datetime.utcnow()`

**Mensaje:**
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

**Solución:** ✅ **YA CORREGIDO**
- Actualizado a `datetime.now(timezone.utc)` en `api.py`
- Compatible con Python 3.12+

---

### 2. JWT Security Warning: HMAC Key Too Short

**Mensaje:**
```
InsecureKeyLengthWarning: The HMAC key is 27 bytes long, 
which is below the minimum recommended length of 32 bytes for SHA256.
```

**Causa:** La `SECRET_KEY` en `.env` es demasiado corta.

**Solución:**

#### Opción A: Generar una clave automáticamente (RECOMENDADO)

```bash
python generate_secret_key.py
```

Esto genera una clave segura de 64 caracteres. Cópiala y:
1. Abre `.env`
2. Reemplaza la línea `SECRET_KEY=...` con la nueva clave
3. Guarda el archivo
4. Reinicia la aplicación

#### Opción B: Configurar manualmente

Edita `.env`:
```bash
# ❌ MAL (demasiado corta)
SECRET_KEY=my-secret

# ✅ BIEN (mínimo 32 caracteres)
SECRET_KEY=my-super-secret-key-that-is-at-least-32-characters-long-and-random
```

---

### 3. Node Deprecation Warning: `util._extend` 

**Mensaje:**
```
(node:74716) [DEP0060] DeprecationWarning: The `util._extend` API is deprecated
```

**Causa:** Paquetes con versiones antiguas en `node_modules`.

**Solución:**

Actualiza las dependencias del frontend:

```bash
cd chatdev

# Opción 1: Reinstalar todo (RECOMENDADO)
rm -r node_modules package-lock.json
npm install

# Opción 2: Solo actualizar
npm update
```

✅ **YA ACTUALIZADO en package.json** (Vite 5.2.0, Tailwind 3.4.1, etc.)

---

## ✅ Checklist de Seguridad

Antes de ejecutar en producción:

- [ ] **SECRET_KEY:** Generada con `generate_secret_key.py` (mín. 32 bytes)
- [ ] **API Key:** `OPENROUTER_API_KEY` está en `.env` (NO en el repo)
- [ ] **CORS:** Configurado correctamente en `api.py`
- [ ] **HTTPS/WSS:** Usar en producción (nginx/Let's Encrypt)
- [ ] **Base de datos:** Usar PostgreSQL en producción (no SQLite)
- [ ] **Logs:** No contienen datos sensibles

---

## 📋 Ejemplo de .env Seguro

```bash
# OpenRouter API (obtener en https://openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-abc123def456...

# JWT Secret (generar con: python generate_secret_key.py)
SECRET_KEY=aB3$xY9#mK2@pQ8!vW5%rT7^nL4&sJ6*uI1(oP0)E
```

---

## 🚀 Ejecutar sin Warnings

Después de configurar correctamente:

```bash
# Terminal 1 - Backend
python api.py

# Terminal 2 - Frontend  
cd chatdev
npm run dev
```

Deberías ver solo mensajes informativos, sin warnings de seguridad.

---

## 📚 Referencias

- [Python datetime.utcnow() deprecation](https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow)
- [JWT HMAC Key Length (RFC 7518)](https://tools.ietf.org/html/rfc7518#section-3.2)
- [Node.js util._extend deprecation](https://nodejs.org/api/util.html#util_util_extend_target_source)

---

## ❓ Preguntas Frecuentes

**P: ¿Qué pasa si no arreglo estos warnings?**  
R: La app sigue funcionando, pero es menos segura y podría tener problemas en futuras versiones de Python/Node.

**P: ¿Puedo usar cualquier SECRET_KEY?**  
R: Debe ser:
- Mínimo 32 caracteres para SHA256
- Aleatoria (no frases simples)
- Única (no compartir entre ambientes)

**P: ¿Dónde guardo la SECRET_KEY generada?**  
R: Solo en `.env`. NUNCA en el código ni en git.

---

**Última actualización:** 2026-07-27
