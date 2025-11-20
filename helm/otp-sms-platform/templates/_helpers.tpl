{{/*
Expand the name of the chart.
*/}}
{{- define "otp-sms-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "otp-sms-platform.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "otp-sms-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "otp-sms-platform.labels" -}}
helm.sh/chart: {{ include "otp-sms-platform.chart" . }}
{{ include "otp-sms-platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "otp-sms-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "otp-sms-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
PostgreSQL connection string
*/}}
{{- define "otp-sms-platform.postgresql.url" -}}
{{- if .Values.postgresql.enabled -}}
postgresql://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ include "otp-sms-platform.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- end -}}
{{- end }}

{{/*
PostgreSQL asyncpg connection string
*/}}
{{- define "otp-sms-platform.postgresql.asyncpgUrl" -}}
{{- if .Values.postgresql.enabled -}}
postgresql+asyncpg://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ include "otp-sms-platform.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- end -}}
{{- end }}

{{/*
Redis host
*/}}
{{- define "otp-sms-platform.redis.host" -}}
{{- if .Values.redis.enabled -}}
{{ include "otp-sms-platform.fullname" . }}-redis-master
{{- end -}}
{{- end }}

{{/*
RabbitMQ host
*/}}
{{- define "otp-sms-platform.rabbitmq.host" -}}
{{- if .Values.rabbitmq.enabled -}}
{{ include "otp-sms-platform.fullname" . }}-rabbitmq
{{- end -}}
{{- end }}
