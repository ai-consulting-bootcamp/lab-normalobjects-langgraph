# Lab Proof: NormalObjects Complaint Processor

## 1. What I built
El programa sigue un flujo de atención de reclamaciones y utiliza LORE, como fuente para poder elaborar una respuesta basada en esa fuente. La ruta a seguir es Válida: intake → validate → investigate → resolve → close → END.
No válida: intake → validate → reject → END. El código se encuentra en Lab_normalobjects_langgraph.ipynb.

## 2. Query
The Downside Up portal opens at different times each day. How do I predict when?

## 3. Evidence (workflow path + log lines + lore used)
### Complaint and validation
```text
COMPLAINT:
The Downside Up portal opens at different times each day. How do I predict when?

CATEGORY:
portal

VALIDATION_REASON:
Categoría aceptada: portal
```

### Source used
Source: `LORE["portal"]`

```text
Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.
```

### Investigation output
```text
The source states that portals open when the barrier between worlds is weak and that their timing follows electrical activity, not the clock. Therefore, predicting when the Downside Up portal opens based on a specific time each day is not possible, as it depends on electrical activity rather than a set schedule.
```

### Execution logs
```text
[INTAKE] Processing complaint...
[INTAKE] Categorized as: portal
[VALIDATE] Checking category...
[INVESTIGATE] Reading source...
[RESOLVE] Preparing resolution...
[CLOSE] Processing completed.
```

### Workflow path and completion
```text
WORKFLOW_PATH:
['intake', 'validate', 'investigate', 'resolve', 'close']

STATUS:
closed

CLOSURE:
Complaint processing completed.
```

## 4. Final output
```text
Resolution:
The investigation indicates that portals open when the barrier between worlds is weak, with their timing influenced by electrical activity rather than a fixed schedule. Consequently, the available information does not provide a method for predicting when the Downside Up portal will open, as it cannot be determined based on specific times each day. This limitation underscores the unpredictability of portal openings and the challenges in establishing a reliable prediction framework.
```
## 5. Trace (which claim comes from which lore line?)
The source states that portals open when the barrier between worlds is weak and that their timing follows electrical activity, not the clock. La fuente no afirma que la apertura de los portales sea impredecible. El modelo ha convertido una información limitada en una conclusión más fuerte. Este es un fallo real

## 6. Failure or limitation
Para el apartado 6: El fallo apareció cuando en resolve se muestra que la afirmación de apertura de los portales es impredecible cuando en la fuente no se indica ello. Se ajustó el prompt pero esa afirmación de impredecibilidad persistió. Y si bien se cerró la consulta, eso solo confirma que el flujo terminó pero no que las afirmaciones tengan respaldo.
Crear investigated_state no produjo el fallo: solo preparó el expediente para repetir la prueba. La afirmación reapareció al ejecutar resolve_node(investigated_state).
La prueba no demostró que el nuevo prompt evitara el fallo. Comprobamos que la afirmación sobre la impredecibilidad de los portales persistió.

## 7. LangGraph vs. one LLM call
| | LangGraph | One LLM call |
|---|---|---|
|Same answer every run? |Solo hemos realizado una ejecución de esta comparación. No podemos asegurar repetibilidad; temperature=0 tampoco la garantiza |No comprobado: solo una ejecución |
|Invalid complaint rejected? |Status: rejected |generó una historia humorística |
|Path visible? |workflow_path|No se mostró un registro de nodos |
|Source of each claim? |Tener LORE guardado permite contrastar afirmaciones, pero ya detectamos algunas sin respaldo. |no mostró fuentes verificables. Sugirió recopilar datos históricos y consultar una comunidad, pero no aportó datos, documentos ni referencias concretas |
|Best for which client case? |tramitar solicitudes con reglas |generar ideas creativas |