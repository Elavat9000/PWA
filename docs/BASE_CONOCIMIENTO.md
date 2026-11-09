# Base de conocimiento de DriveSmart

Investigación y revisión: **8 de noviembre de 2026**.
Modo de negocio confirmado: **demostración sin pagos**.

## Contenido disponible

El catálogo tiene **307 temas y 456 formulaciones únicas normalizadas**, organizadas
en **27 categorías** y niveles básico, intermedio y avanzado. Una formulación es una
manera de preguntar, no una política diferente por tener variantes.

- **245 formulaciones publicadas** sobre funciones y límites comprobados de la beta.
- **211 formulaciones pendientes** sobre decisiones de una operación comercial futura.
- Las pendientes tienen la respuesta vacía: la validación existente impide publicarlas
  sin escribir una respuesta. Las indicaciones de revisión se guardan en `review_notes`
  del catálogo fuente, no en la respuesta al cliente.

Clasificación, niveles, agrupaciones, fuentes y revisión están en
`assistant/data/knowledge_base.json`. SQLite conserva preguntas, respuestas y estados;
no se añadieron columnas de clasificación ni migraciones. Admin conserva su filtro
por estado y búsqueda de texto.

## Categorías

| Categoría | Temas | Formulaciones | Estado inicial |
|---|---:|---:|---|
| Accesorios accesibilidad | 9 | 12 | PENDIENTE |
| Administracion | 10 | 11 | PUBLICADA |
| Asistente | 16 | 24 | PUBLICADA |
| Atencion comercial | 2 | 6 | PENDIENTE |
| Cambios cancelaciones | 13 | 15 | PENDIENTE |
| Caracteristicas | 7 | 7 | PUBLICADA |
| Catalogo | 10 | 10 | PUBLICADA |
| Combustible kilometraje | 12 | 15 | PENDIENTE |
| Conductores usos | 14 | 21 | PENDIENTE |
| Costos | 17 | 22 | PUBLICADA |
| Cuentas | 15 | 27 | PUBLICADA |
| Disponibilidad | 10 | 10 | PUBLICADA |
| Electricos especiales | 8 | 8 | PENDIENTE |
| Empresas facturacion | 9 | 11 | PENDIENTE |
| Entrega devolucion | 15 | 22 | PENDIENTE |
| Estados historial | 10 | 18 | PUBLICADA |
| Fechas | 15 | 17 | PUBLICADA |
| Filtros | 12 | 15 | PUBLICADA |
| Funciones basicas | 8 | 39 | PUBLICADA |
| Garantias pagos | 15 | 28 | PENDIENTE |
| Incidencias reales | 14 | 16 | PENDIENTE |
| Introduccion | 8 | 18 | PUBLICADA |
| Privacidad comercial | 6 | 6 | PENDIENTE |
| Pwa soporte | 11 | 12 | PUBLICADA |
| Requisitos reales | 14 | 27 | PENDIENTE |
| Seguros coberturas | 16 | 24 | PENDIENTE |
| Solicitudes | 11 | 15 | PUBLICADA |

## Criterio editorial y fuentes

Las respuestas públicas se redactaron a partir del funcionamiento comprobado y de
los archivos locales indicados por tema. Las tarifas, inventario y disponibilidad no
se fijan como respuestas estáticas: pertenecen a los registros y validaciones reales.

La investigación externa identifica preguntas y escenarios; no importa respuestas
comerciales. No se adoptaron edades mínimas, depósitos, deducibles, plazos, teléfonos,
sucursales ni condiciones de otro proveedor como si fueran de DriveSmart. La redacción
es propia; no se copiaron páginas completas.

Fuentes oficiales consultadas:

- [Enterprise México — FAQ](https://enterprise.mx/preguntas-frecuentes): reservas, requisitos, coberturas, accesorios e incidencias.
- [Hertz México — FAQ](https://www.hertzmexico.com/preguntas-frecuentes/): cambios, disponibilidad, garantías y pagos.
- [Avis México — FAQ](https://avis.mx/preguntas-frecuentes): costo, protecciones, garantías y atención.
- [SIXT México — Condiciones](https://www.sixt.com.mx/shared/t-c/sixt_MX_es.pdf): requisitos, recogida, pagos, extensiones y datos.
- [Alamo México — FAQ](https://alamo.com.mx/es/preguntas): requisitos, reservas, conductores, reembolsos e incidencias.
- [Alamo México — Políticas](https://alamo.com.mx/es/preguntas/condiciones-y-politicas-de-renta): coberturas, accesorios, combustible y devolución.
- [Alamo — FAQ en español](https://www.alamo.com/es/atencion-al-cliente/preguntas-frecuentes.html): equipamiento, mascotas, kilometraje y atención.
- [Europcar México — FAQ](https://www.europcar.com.mx/faq): documentos, garantías, accesorios, fronteras y facturación.

Son ocho fuentes, de seis marcas. Sus condiciones pueden cambiar y variar por país
o sucursal. Sirven como mapa de temas, no como reglas de DriveSmart.

En cada tema pendiente, `review_notes` indica qué debe decidir el responsable.
Las respuestas comerciales futuras deben verificarse con quien opere el servicio,
proveedor y documentación vigentes antes de publicarlas. Las preguntas de emergencia
siguen pendientes: el asistente no se presenta como asistencia real ni inventa teléfonos.

## Carga repetible y protección de ediciones

```powershell
.venv\Scripts\python.exe manage.py load_knowledge_base --dry-run
.venv\Scripts\python.exe manage.py load_knowledge_base
```

El comando valida el catálogo completo y utiliza una transacción. Conserva las
entradas existentes, respuestas humanas, estados, usuario de origen y fechas.
No elimina registros ni sobrescribe ediciones. Las variantes nuevas de un tema
público heredan su respuesta existente de referencia y no reemplazan un borrador humano.

Para completar únicamente pendientes vacías que coinciden con un tema público
comprobado del catálogo, existe esta opción explícita:

```powershell
.venv\Scripts\python.exe manage.py load_knowledge_base --complete-pending
```

No publica las políticas comerciales ni sustituye respuestas no vacías.
En la carga inicial se crearon **443 registros**, se conservaron intactas las ocho
respuestas originales y se completaron cinco pendientes vacías sobre saludo, ayuda
y orientación de precios. Se conservaron sus identificadores, preguntas, usuario y
fecha original. La segunda carga produjo **cero cambios**.

`load_faq` sigue disponible para sus ocho FAQ originales. En una instalación nueva,
`load_knowledge_base` ya incluye esas ocho preguntas y todo el catálogo ampliado.

## Mantenimiento administrativo

1. Entrar a `/admin/assistant/knowledgeentry/` con los permisos correspondientes.
2. Filtrar Estado = Pendiente y buscar el tema.
3. Revisar categoría, fuentes e indicaciones en el JSON.
4. Escribir una respuesta comprobada, aplicable a DriveSmart y comprensible.
5. Cambiar a Publicada y guardar. Una respuesta vacía no se publica.
6. Probar la pregunta y sus variantes. Al editar, revisar las formulaciones del mismo
   tema: las entradas existentes no se sincronizan ni sobrescriben automáticamente.
   Mantener también el catálogo para instalaciones futuras.

La aplicación no consulta estas fuentes por internet durante el chat. Sigue siendo
local, sin APIs de IA, embeddings ni modelos de lenguaje. El motor no se modificó:
compara textos conservadoramente y cada mensaje es independiente. Una base más amplia
no garantiza interpretar cualquier frase ni añade memoria conversacional.

## Verificación ejecutada

- **88/88 pruebas Django aprobadas**, incluidas nueve pruebas nuevas de integración del catálogo.
- Recuperación de las 245 formulaciones públicas y exclusión de las 211 comerciales al comparar con conocimiento público.
- Protección de borradores, publicación vacía, ediciones humanas, usuario y fechas; simulación sin escrituras y recarga sin duplicados.
- El precio del vehículo mantiene prioridad y refleja modificaciones del registro.
- Compatibilidad con variantes y errores de escritura de las FAQ originales.
- `check` correcto, migraciones completas y ningún cambio de esquema.
- Siete consultas HTTP reales con CSRF y `Cache-Control: no-store`: saludo, reserva, acceso, costo general, seguro, WhatsApp y precio de Corolla.
- Respuestas entre 4.2 y 115.7 ms en esa muestra local; no es una prueba de carga.
- SQLite íntegra y vehículos/rentas sin cambios respecto al respaldo previo.

El respaldo anterior y la verificación posterior se conservaron fuera del proyecto,
en una carpeta temporal con prefijo `DriveSmart_conocimiento_20261108_`.
No se recrearon resultados de QA, navegadores ni dependencias Node dentro del proyecto.
No se creó commit, remoto ni push. SQLite permanece ignorada en Git: el JSON y su
comando permiten reproducir el contenido.
