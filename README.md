# SE-Proyecto-Final-Multiagente

# ForgeFlow ERP

### *Sistema Experto Multiagente para el Control Operativo, Gestión de Inventarios y Planificación de la Producción Metalmecánica*

ForgeFlow ERP es un sistema de gestión empresarial inteligente (ERP) diseñado específicamente para optimizar el flujo de trabajo, la administración de inventarios y el proceso de cotización técnica en talleres de maquinado y manufactura flexográfica. 

A diferencia de los ERPs tradicionales basados en formularios rígidos, **ForgeFlow ERP** utiliza una arquitectura de **Sistemas Expertos Multiagente** que permite interactuar con el sistema mediante lenguaje natural y técnico (procesamiento a través de un chat interno), automatizando decisiones complejas de ingeniería, almacén y logística de piso.

---

## 🚀 Características Principales

* **Interfaz Basada en Chat Técnico (NLP):** Procesamiento de requerimientos internos mediante lenguaje natural. El sistema entiende conceptos técnicos reales del taller como *"rodillo de impresión"*, *"yunque"*, *"engrane con mamelón"*, *"ranurado de bronce"*, entre otros.
* **Motor de Inferencia Recursivo (BOM):** Capacidad para desarmar lógicamente ensambles complejos. Si se solicita un rodillo compuesto, el motor analiza dinámicamente sus dependencias (materiales y herramental de las subpiezas) sin duplicar código.
* **Discriminación de Servicios (Fabricación vs. Reparación):** El sistema adapta automáticamente las fórmulas de costos. Si es una reparación, descuenta el costo de materia prima y aplica tarifas específicas de ajuste de precisión.
* **Planificador de Producción Automático (Scheduler):** Calcula los tiempos de maquinado estimados basándose en la dureza del material y la complejidad de la pieza, consultando la cola de trabajo actual en el taller para proyectar una **fecha de entrega real**.
* **Gestión Dinámica de Inventario y Cadena de Suministro:** Permite actualizar existencias de materiales (rack) y herramientas (brocas, buriles, insertos) directamente desde el chat. Si detecta desabasto en una cotización, genera automáticamente una orden de compra en formato de texto para el proveedor adecuado.