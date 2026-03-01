{{/*
Expand the name of the chart.
*/}}
{{- define "demo-rag.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}
