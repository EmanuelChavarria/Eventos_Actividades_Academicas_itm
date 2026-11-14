# Guía de Trabajo Práctico Experimental — Proyecto Final 04

**Organización de eventos y actividades académicas — Desarrollo e integración de aplicaciones y servicios web**

---

| Campo | Valor |
|---|---|
| **Código de guía** | PF-04 |
| **Laboratorio** | Laboratorio de Aplicaciones y Servicios Web |
| **Tiempo de trabajo práctico estimado** | Según cronograma del curso |
| **Asignatura** | Aplicaciones y Servicios Web |
| **Programa académico** | Tecnología en Desarrollo de Software |
| **Elaborado por** | Juan Carlos Morales Guerra |
| **Revisado por** | Juan Carlos Morales Guerra |
| **Versión** | 001 |
| **Fecha** | 04-11-2026 |

---

## 1. Competencias, Contenido Temático e Indicador de Logro

| Competencias | Contenido Temático | Indicador de Logro |
|---|---|---|
| Diseñar, desarrollar e integrar aplicaciones y servicios web mediante tecnologías frontend y backend, implementando APIs REST, persistencia de datos, validaciones y pruebas de funcionamiento, a partir de los requisitos de un problema organizacional. | Arquitectura cliente-servidor. Desarrollo frontend y backend. API REST. Métodos HTTP y códigos de respuesta. Operaciones CRUD. Validación de datos. Persistencia y bases de datos relacionales. Integración y consumo de servicios web. Manejo de errores. Pruebas de APIs y funcionalidades. Git y GitHub. Documentación técnica. | El equipo implementa una aplicación web funcional que integra una interfaz de usuario, una API REST y una base de datos; ejecuta operaciones de consulta y modificación de información, aplica reglas de negocio y validaciones, verifica su funcionamiento mediante pruebas y documenta su desarrollo en GitHub. |

---

## 2. Fundamento Teórico

Una **aplicación web** permite que los usuarios interactúen con un sistema mediante un navegador. En una arquitectura **cliente-servidor**, el frontend presenta información y recibe acciones de los usuarios, mientras el backend procesa solicitudes, aplica reglas de negocio y accede a los datos.

Una **API REST** permite exponer recursos mediante HTTP para que el frontend y otros clientes intercambien información con el backend. Los métodos `GET`, `POST`, `PUT`, `PATCH` y `DELETE` representan operaciones sobre recursos cuando corresponda; los códigos de estado HTTP comunican el resultado de cada solicitud. **CRUD** describe las operaciones de creación, consulta, actualización y eliminación, pero no todas deben estar habilitadas para cualquier recurso: dependen de las reglas del proceso.

La **persistencia de datos** permite conservar la información más allá de la ejecución de la aplicación. El diseño de una base de datos relacional requiere identificar entidades, claves y relaciones, así como aplicar restricciones para mantener la consistencia de los registros.

La **integración frontend–API–base de datos** requiere intercambiar datos reales entre los componentes, gestionar estados de la interfaz, validar entradas y tratar errores. Las validaciones del servidor deben proteger la integridad de los datos incluso si una solicitud se envía sin utilizar la interfaz web.

Las **pruebas de servicios web** verifican las respuestas de los endpoints ante solicitudes válidas, entradas incorrectas, recursos inexistentes y acciones no autorizadas. En este proyecto, las verificaciones se realizarán mediante **pruebas funcionales documentadas**, utilizando las herramientas de consulta HTTP y de ejecución de la aplicación trabajadas durante el curso. No se exige automatizar su ejecución.

**Git** registra los cambios del proyecto. **GitHub** facilita el trabajo colaborativo mediante ramas, commits y *pull requests*. Cada cambio debe ser comprensible y tener relación con el trabajo implementado o corregido.

El **levantamiento de requisitos** y los criterios de aceptación se utilizarán para delimitar qué comportamiento debe implementar la aplicación. En este proyecto son insumos para el desarrollo y las pruebas, no el producto principal de la asignatura.

---

## 3. Objetivos

### Objetivo General

Desarrollar e integrar una aplicación web para organizar eventos y actividades académicas de una institución educativa, mediante una interfaz frontend, una API REST y una base de datos, verificando su funcionamiento con pruebas funcionales documentadas y registrando el desarrollo en GitHub.

### Objetivos Específicos

- Delimitar el proceso de organización e inscripción a eventos mediante requisitos, reglas de negocio y criterios de aceptación verificables.
- Diseñar la arquitectura cliente-servidor, las interfaces, el modelo de datos y los servicios web necesarios.
- Implementar una API REST con métodos HTTP, validaciones, manejo de errores y operaciones coherentes con el proceso.
- Implementar una interfaz web para publicar actividades, consultar información, inscribirse y registrar asistencia.
- Mantener persistencia de eventos, cupos, inscripciones, participantes y registros de asistencia definidos en el diseño.
- Aplicar reglas de disponibilidad de cupos y evitar inscripciones incompatibles con las restricciones aprobadas.
- Integrar frontend, backend y base de datos en flujos completos de creación, inscripción y asistencia.
- Diseñar, ejecutar y documentar pruebas funcionales de servicios web, reglas de negocio e integración.
- Utilizar Git y GitHub con ramas, commits descriptivos y pull requests documentados.
- Documentar instalación, servicios web y evidencias del cumplimiento de las condiciones de aceptación.

---

## 4. Recursos Requeridos

### Equipos

- Computador personal o estación de trabajo con acceso a Internet.

### Herramientas de Software

- Editor de código o IDE.
- Git y cuenta en GitHub.
- Lenguaje, framework frontend y framework backend seleccionados y justificados por el equipo.
- Sistema de gestión de bases de datos seleccionado por el equipo.
- Herramientas de consulta HTTP y verificación de endpoints utilizadas durante el curso (por ejemplo, la interfaz de documentación interactiva de la API o un cliente HTTP conocido por el equipo).

### Recursos suministrados

- Enunciado del problema y condiciones de aceptación obligatorias de esta guía.
- Sesión de levantamiento de requisitos con el docente en el papel de representante de la organización.
- Revisión y aprobación del alcance por parte del docente.

### Restricciones técnicas comunes

- La aplicación debe incluir una **interfaz web**, un **backend con API REST** y **persistencia en una base de datos**.
- Debe existir comunicación real entre interfaz, API y base de datos; no se aceptan pantallas con datos simulados como sustituto de las funciones obligatorias.
- El diseño, las rutas HTTP, la estructura de tablas y la tecnología concreta deberán ser definidos y documentados por el equipo.
- Deben ejecutarse y documentarse las pruebas funcionales de la Actividad 6. No se exigen frameworks de pruebas automatizadas ni herramientas de CI.
- No se exige despliegue en la nube ni uso de Docker.

---

## 5. Aspectos de Seguridad

La actividad corresponde a desarrollo de software y no implica riesgos físicos o químicos propios de prácticas experimentales.

- No incorporar contraseñas, tokens, claves o cadenas de conexión reales en el repositorio.
- Mantener los archivos locales `.env` fuera del control de versiones y proporcionar un `.env.example` sin secretos, cuando corresponda.
- Utilizar datos ficticios para demostrar los casos de uso; no publicar información personal real de usuarios de la organización.
- Validar las entradas tanto en el servidor como en los puntos de interacción que resulten necesarios.
- Definir y aplicar permisos acordes con los actores identificados, evitando que un usuario acceda o modifique información no autorizada.
- Evitar que los registros y mensajes de error revelen información sensible.

---

## 6. Procedimiento o Metodología para el Desarrollo

El proyecto se desarrolla de forma colaborativa. Los equipos, fechas, hitos de entrega y condiciones de sustentación serán los comunicados por el docente. El trabajo debe conservar evidencias de las decisiones y de la participación individual.

### Actividad 1: Comprensión del Problema y Delimitación del Alcance

#### A. Contexto

Una institución educativa organiza conferencias, talleres, seminarios y capacitaciones dirigidas a estudiantes, docentes y otros integrantes de su comunidad. Diferentes áreas coordinan la programación, divulgación, recepción de inscripciones y registro de asistencia de estas actividades.

#### B. Situación actual

Las actividades se anuncian por diferentes medios y las inscripciones se reciben mediante formularios o mensajes independientes. Esto dificulta conocer el número real de personas inscritas, controlar los cupos disponibles y evitar registros duplicados. Los organizadores también tienen problemas para consultar listas actualizadas y consolidar la asistencia al finalizar cada evento.

#### C. Actores involucrados

- **Participante:** persona que consulta las actividades y solicita inscribirse en una de ellas.
- **Organizador:** personal que programa y administra las actividades, revisa inscripciones y registra asistencia.
- **Coordinación:** personal encargado de supervisar el desarrollo de eventos y consultar información consolidada.

Estos actores representan responsabilidades generales. El equipo definirá los permisos, datos, estados, reglas de cupos y excepciones durante el levantamiento de requisitos.

#### D. Problema a resolver

La institución necesita una solución web para organizar y dar seguimiento a sus actividades académicas, desde la creación y publicación del evento hasta la inscripción de participantes, la administración de cupos y el registro de asistencia, conservando información consistente para los organizadores y la coordinación.

#### E. Límites obligatorios del alcance

La aplicación debe cubrir **creación y publicación de actividades, consulta de eventos, inscripción de participantes, control de cupos y registro de asistencia**. La información debe persistir y permitir distinguir personas inscritas, disponibilidad de cupos y asistencia registrada. El sistema debe impedir que se exceda el cupo aprobado y gestionar inscripciones duplicadas de acuerdo con reglas definidas y aprobadas.

El proyecto se limita a la **organización y seguimiento de eventos académicos**. No exige pasarelas de pago, transmisión de videoconferencias, envío de mensajes SMS o WhatsApp, generación de certificados firmados, integración con sistemas institucionales ni lectura de códigos QR. Estas funciones podrían considerarse extensiones, pero no sustituyen el proceso mínimo.

#### F. Condiciones de aceptación obligatorias

| ID | Condición | Demostración esperada |
|---|---|---|
| CA-01 | El personal autorizado puede crear y publicar actividades académicas. | Una actividad se registra, conserva sus datos y aparece en el catálogo de eventos publicados. |
| CA-02 | Los participantes pueden consultar los eventos y su disponibilidad. | La interfaz muestra información de los eventos y cupos coherente con las inscripciones almacenadas. |
| CA-03 | Un participante puede inscribirse en una actividad. | La inscripción válida queda persistida y puede consultarse desde la aplicación. |
| CA-04 | El sistema administra cupos e impide inscripciones incompatibles. | Se rechaza una inscripción que exceda el cupo o incumpla una regla aprobada, sin alterar indebidamente los registros. |
| CA-05 | El personal autorizado puede registrar asistencia y consultar la lista de participantes. | Se conserva la relación entre actividad, participante e información de asistencia. |
| CA-06 | La coordinación puede consultar información consolidada de eventos, inscripciones y asistencia. | Se presentan resultados de varias actividades con sus cantidades y estados coherentes. |

**Estas condiciones delimitan el producto, pero no constituyen una especificación cerrada.** El equipo definirá qué datos tiene cada evento, cómo se publican, quién puede inscribirse, las restricciones sobre cupos, reglas para inscripciones repetidas o cancelaciones, el registro de asistencia, estados y autorizaciones. No basta con un CRUD de eventos sin inscripción, control de cupos y asistencia.

### Actividad 2: Definición de Requisitos para el Desarrollo

1. Preparar preguntas para una entrevista con el docente en el rol de representante de la organización.
2. Realizar la entrevista y registrar preguntas, respuestas, acuerdos y cuestiones pendientes.
3. Identificar actores, procesos, necesidades, reglas de negocio y restricciones.
4. Formular requisitos funcionales identificados como `RF-XX` y no funcionales como `RNF-XX`.
5. Elaborar historias de usuario o casos de uso con criterios de aceptación verificables.
6. Priorizar requisitos y proponer un alcance realizable, sin excluir las condiciones CA-01 a CA-06.
7. Presentar la especificación al docente para su revisión y aprobación.

**Entrega:** `docs/requisitos.md`, registro breve de entrevista, alcance y criterios de aceptación aprobados. Este documento delimita qué se implementará; no se evaluará por su extensión, sino por su claridad y utilidad para desarrollar y probar la aplicación. Los supuestos no confirmados deben identificarse.

### Actividad 3: Diseño de la Aplicación y de los Servicios Web

1. Proponer una arquitectura que identifique frontend, backend, API REST y persistencia.
2. Diseñar el modelo de datos, con entidades, atributos, claves y relaciones.
3. Diseñar los recorridos principales de los actores y los prototipos de interfaz.
4. Especificar los recursos de la API, métodos HTTP, formatos de solicitud y respuesta, validaciones y errores esperados.
5. Definir cómo se aplicarán las reglas de negocio y las restricciones de acceso.
6. Documentar las decisiones técnicas y su correspondencia con los requisitos.

**Entrega:** `docs/diseno.md`, diagramas, prototipos, modelo de datos y especificación de API. No se proporciona una estructura de carpetas obligatoria; el equipo deberá justificar cómo organiza las responsabilidades de su aplicación.

### Actividad 4: Desarrollo de Frontend, API REST y Persistencia

1. Configurar el repositorio y los entornos de desarrollo.
2. Implementar persistencia y relaciones entre eventos, inscripciones y participantes según el diseño aprobado.
3. Desarrollar la API REST con respuestas y códigos HTTP apropiados.
4. Implementar las interfaces web necesarias para cumplir los casos aprobados.
5. Integrar interfaz, API y base de datos.
6. Incorporar validación de datos, manejo de errores y controles de acceso definidos.
7. Verificar el recorrido completo de creación y publicación de un evento, inscripción y registro de asistencia.

**Entrega:** código funcional de frontend y backend, base de datos configurada, documentación de endpoints, instrucciones reproducibles de ejecución y evidencia de un flujo completo desde la interfaz hasta la persistencia. Las operaciones CRUD deben implementarse únicamente cuando estén justificadas por el proceso.

### Actividad 5: Control de Versiones y Trabajo Colaborativo

Cada equipo deberá:

- Utilizar un repositorio de GitHub accesible para evaluación.
- Utilizar ramas para desarrollar cambios y *pull requests* para integrarlos.
- Redactar commits descriptivos que permitan comprender la evolución del sistema.
- Documentar en los pull requests el propósito, cambios realizados, pruebas efectuadas y requisitos asociados.
- Conservar evidencia de revisiones del código entre integrantes, cuando el equipo tenga más de una persona.
- Identificar los aportes verificables de cada integrante.

No se considerará evidencia suficiente una única carga final del proyecto, un historial compuesto exclusivamente por commits genéricos o una lista de contribuciones sin respaldo en GitHub.

### Actividad 6: Pruebas Funcionales de API, Reglas de Negocio e Integración

Diseñar y ejecutar **pruebas funcionales documentadas** de la API REST, las reglas de inscripción y cupos, y la integración entre frontend, API y base de datos. Las verificaciones deben cubrir casos exitosos, entradas inválidas, recursos inexistentes, actuaciones no autorizadas y consistencia de inscripciones y asistencia. Se podrán utilizar las herramientas HTTP y de ejecución trabajadas durante el curso; **no se exige automatización de pruebas**.

| # | Prueba mínima | Evidencia esperada |
|---|---|---|
| 1 | Registro y publicación de actividad válida | Evento persistido y visible en el catálogo |
| 2 | Creación de actividad con datos inválidos | Entrada rechazada sin persistencia inválida |
| 3 | Consulta de catálogo y detalle de evento | Datos reales recuperados correctamente |
| 4 | Consulta de evento inexistente | Respuesta de error controlada |
| 5 | Inscripción válida de un participante | Inscripción persistida y recuperable |
| 6 | Inscripción con datos inválidos | Solicitud rechazada de forma controlada |
| 7 | Intento de inscripción con cupo agotado | Operación rechazada y cupo conservado |
| 8 | Intento de inscripción duplicada no permitida | Operación rechazada según reglas aprobadas |
| 9 | Gestión de evento o asistencia sin autorización | Operación impedida |
| 10 | Registro y consulta de asistencia | Asistencia persistida y asociada a evento y participante |
| 11 | Información consolidada y consistencia de datos | Totales de cupos, inscripciones y asistencia coherentes |
| 12 | Integración interfaz–API–base de datos | Flujo completo de creación, inscripción y asistencia demostrado |

Para cada prueba se documentará: identificador, requisito asociado, condiciones iniciales, pasos, datos de entrada, resultado esperado, resultado obtenido, estado (aprobada/fallida), evidencia y, cuando aplique, método y código HTTP. Las evidencias podrán ser capturas de solicitudes y respuestas, consultas de datos o capturas de la interfaz; deben permitir reproducir la verificación.

**No se exigen pruebas automatizadas, Postman CLI, Newman, pytest, Jest, Vitest ni GitHub Actions.**

### Actividad 7: Matriz de Trazabilidad y Sustentación

Crear `docs/trazabilidad.md` con la correspondencia entre condiciones obligatorias, requisitos, componentes implementados, pull requests y pruebas.

| Condición | Requisito aprobado | Implementación (ruta/componente) | Pull request | Prueba |
|---|---|---|---|---|
| CA-01 | Por completar | Por completar | Por completar | Por completar |
| CA-02 | Por completar | Por completar | Por completar | Por completar |
| CA-03 | Por completar | Por completar | Por completar | Por completar |
| CA-04 | Por completar | Por completar | Por completar | Por completar |
| CA-05 | Por completar | Por completar | Por completar | Por completar |
| CA-06 | Por completar | Por completar | Por completar | Por completar |

Durante la sustentación, el equipo deberá demostrar un flujo completo de creación de evento, inscripción y registro de asistencia, explicar las principales decisiones de diseño, repetir pruebas funcionales seleccionadas y mostrar el historial de contribuciones. El docente podrá preguntar individualmente a los integrantes sobre su participación.

---

## 7. Resultado Esperado del Proyecto

Al finalizar, cada equipo deberá disponer de:

- Una aplicación web funcional con frontend, API REST y base de datos.
- Una definición breve de requisitos y un diseño que permitan comprobar por qué se implementaron los componentes y servicios seleccionados.
- Un proceso de gestión de actividades académicas, desde la publicación hasta el registro de asistencia, que cumpla CA-01 a CA-06.
- Validaciones, autorizaciones y control de cupos según las reglas aprobadas.
- Pruebas funcionales ejecutadas y resultados documentados.
- Un historial Git verificable de ramas, commits y pull requests.
- Una matriz de trazabilidad de requisitos, implementación y pruebas.
- Un README que permita instalar, ejecutar, revisar y evaluar la solución.

**Criterio de cumplimiento:** una pantalla aislada, una API sin interfaz, datos únicamente simulados o un CRUD genérico que no represente el proceso de inscripción, cupos y asistencia no constituyen una solución completa.

### Criterios de evaluación

| Criterio | Peso |
|---|---:|
| Delimitación de requisitos y criterios de aceptación | 10 % |
| Diseño de arquitectura, API y modelo de datos | 10 % |
| Implementación frontend, backend, API REST y persistencia; integración funcional | 45 % |
| Pruebas funcionales de servicios web, reglas de negocio y documentación técnica | 20 % |
| Git y GitHub: commits, ramas, pull requests y aportes verificables | 15 % |
| **Total** | **100 %** |

La evaluación priorizará el funcionamiento real y la integración de la aplicación y los servicios web. La documentación de requisitos y diseño debe sustentar el desarrollo, no sustituirlo. La cantidad de pantallas o endpoints, por sí sola, no determina la calidad de la solución.

---

## 8. Parámetros para Elaboración del Informe

El informe final se presentará en formato **`README.md`** dentro del repositorio. No se aceptará como sustituto un informe externo en Word o PDF. Los documentos técnicos complementarios deben conservarse en el repositorio y enlazarse desde el README.

### Contenido del README.md

#### 1. Información General

- Nombre del proyecto y problema seleccionado.
- Integrantes y contribución de cada uno.
- Asignatura, fecha y enlace al repositorio.

#### 2. Descripción del Sistema

- Problema abordado, actores y alcance aprobado.
- Resumen de la solución y de sus restricciones.
- Enlace a `docs/requisitos.md`.

#### 3. Requisitos y Alcance

- Método utilizado para obtener la información.
- Evidencia de entrevista y decisiones confirmadas por el docente.
- Requisitos priorizados, historias de usuario/casos de uso y criterios de aceptación.

#### 4. Arquitectura, Diseño de API y Modelo de Datos

- Diagrama de componentes y responsabilidades.
- Modelo de datos y relaciones.
- Prototipos o capturas de interfaces.
- Justificación de tecnologías y enlaces a `docs/diseno.md`.

#### 5. Configuración del Entorno

- Requisitos de software, dependencias y comandos de instalación.
- Configuración de variables de entorno sin exponer secretos.
- Pasos para preparar la base de datos y ejecutar frontend y backend.
- Datos de prueba ficticios o instrucciones para generarlos.

#### 6. Servicios Web Implementados

Tabla de endpoints reales:

| Método | Ruta | Descripción | Requisito relacionado |
|---|---|---|---|
| Por completar | Por completar | Por completar | Por completar |

Incluir ejemplos de solicitudes y respuestas, validaciones y errores, y enlace a la documentación de API.

#### 7. Pruebas de API e Integración y Evidencias de Funcionamiento

- Tabla de pruebas de endpoints, reglas de negocio e integración con resultados y requisitos asociados.
- Pasos para reproducir las pruebas funcionales con las herramientas utilizadas en el curso.
- Evidencias del proceso completo y de casos inválidos.
- Enlace a la matriz de trazabilidad.

Guardar las evidencias en una carpeta `evidencias/` o enlazar los resultados generados de manera reproducible.

#### 8. Control de Versiones

- Enlace al repositorio y pull requests relevantes.
- Resumen verificable de aportes de cada integrante.
- Referencias a commits, ramas y pull requests que evidencien el desarrollo y la revisión de cambios.

#### 9. Conclusiones y Limitaciones

- Cumplimiento de las condiciones del problema.
- Dificultades técnicas verificadas y soluciones aplicadas.
- Restricciones o comportamientos pendientes dentro del alcance aprobado, si existen.

### Requisitos del Repositorio

El repositorio debe contener, al menos, estos recursos o equivalentes justificados:

```text
README.md
.gitignore
.env.example                  # Si se emplean variables de entorno
docs/
  requisitos.md
  diseno.md
  trazabilidad.md
evidencias/                   # Evidencias de pruebas funcionales y operación
```

También debe contener el código fuente, la definición reproducible de dependencias, los archivos necesarios para preparar la base de datos y las instrucciones para ejecutar la solución. Las pruebas funcionales deben registrarse en el README o en un documento enlazado, indicando pasos y evidencias para reproducirlas. No se deben incluir credenciales reales.

---

## 9. Disposición de Residuos

La actividad descrita en esta guía no genera residuos físicos o químicos. No se requiere un procedimiento específico de disposición de residuos.

---

## 10. Bibliografía

- Git. *Git Documentation*. https://git-scm.com/doc
- GitHub. *GitHub Docs*. https://docs.github.com/
- OpenAPI Initiative. *OpenAPI Specification*. https://spec.openapis.org/oas/latest.html
- MDN Web Docs. *HTTP*. https://developer.mozilla.org/en-US/docs/Web/HTTP
- MDN Web Docs. *Client-server overview*. https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Client-Server_overview
- Chacon, S., & Straub, B. (2014). *Pro Git*. Apress. https://git-scm.com/book/en/v2
