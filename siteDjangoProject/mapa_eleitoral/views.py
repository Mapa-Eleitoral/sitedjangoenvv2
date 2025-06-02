# mapa_eleitoral/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
import json
import os
from django.conf import settings
import folium as fl
from django.utils.safestring import mark_safe
from django.core.cache import cache
import pandas as pd
import numpy as np
from .models import DadoEleitoral  # ou DadoEleitoralRaw

def load_geojson():
    """Carregar dados do GeoJSON (mantém como estava)"""
    cache_key = 'geojson_data'
    geojson_data = cache.get(cache_key)
    
    if geojson_data is None:
        geojson_path = os.path.join(settings.BASE_DIR, 'mapa_eleitoral', 'data', 'Limite_Bairro.geojson')
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        cache.set(cache_key, geojson_data, 3600)  # Cache por 1 hora
    
    return geojson_data

def home_view(request):
    """View principal do mapa eleitoral usando MySQL"""
    
    # Obter lista de partidos únicos do banco
    partidos = list(
        DadoEleitoral.objects
        .values_list('sg_partido', flat=True)
        .distinct()
        .order_by('sg_partido')
    )
    
    # Partido e candidato selecionados
    selected_partido = request.GET.get('partido', 'PRB')
    selected_candidato = request.GET.get('candidato', '')
    
    # Obter candidatos do partido selecionado
    candidatos = list(
        DadoEleitoral.objects
        .filter(sg_partido=selected_partido)
        .values_list('nm_urna_candidato', flat=True)
        .distinct()
        .order_by('nm_urna_candidato')
    )
    
    # Se não há candidato selecionado, usar o primeiro ou o padrão
    if not selected_candidato or selected_candidato not in candidatos:
        selected_candidato = 'CRIVELLA' if 'CRIVELLA' in candidatos else (candidatos[0] if candidatos else '')
    
    # Dados do mapa
    map_html = ""
    candidato_info = {}
    
    if selected_candidato:
        # Buscar dados do candidato no MySQL
        dados_candidato = DadoEleitoral.objects.filter(
            sg_partido=selected_partido,
            nm_urna_candidato=selected_candidato
        )
        
        if dados_candidato.exists():
            # Calcular votos por bairro
            votos_por_bairro = (
                dados_candidato
                .values('nm_bairro')
                .annotate(total_votos=Sum('qt_votos'))
                .order_by('nm_bairro')
            )
            
            # Converter para dicionário para facilitar o uso
            votos_dict = {item['nm_bairro']: item['total_votos'] for item in votos_por_bairro}
            
            # Informações do candidato
            primeiro_registro = dados_candidato.first()
            total_votos = dados_candidato.aggregate(Sum('qt_votos'))['qt_votos__sum'] or 0
            
            candidato_info = {
                'nome': primeiro_registro.nm_urna_candidato,
                'cargo': primeiro_registro.ds_cargo,
                'votos_total': total_votos
            }
            
            # Criar mapa
            mapa = fl.Map(
                location=[-22.928777, -43.423878], 
                zoom_start=10, 
                tiles='CartoDB positron',
                prefer_canvas=True
            )
            
            # CORREÇÃO: Preparar dados para o Choropleth de forma mais segura
            if votos_por_bairro:
                # Criar DataFrame e garantir tipos corretos
                dados_choropleth = []
                for item in votos_por_bairro:
                    bairro = str(item['nm_bairro']) if item['nm_bairro'] else 'N/A'
                    votos = int(item['total_votos']) if item['total_votos'] is not None else 0
                    dados_choropleth.append([bairro, votos])
                
                # Criar DataFrame com tipos explícitos
                df_choropleth = pd.DataFrame(dados_choropleth, columns=['bairro', 'votos'])
                
                # Garantir que a coluna votos é numérica
                df_choropleth['votos'] = pd.to_numeric(df_choropleth['votos'], errors='coerce').fillna(0)
                
                # Debug - remova depois que funcionar
                print("DataFrame choropleth:")
                print(df_choropleth.head())
                print("Tipos:", df_choropleth.dtypes)
                print("Valores únicos votos:", df_choropleth['votos'].unique()[:10])
                
                # Caminho do GeoJSON
                geojson_path = os.path.join(settings.BASE_DIR, 'mapa_eleitoral', 'data', 'Limite_Bairro.geojson')
                
                try:
                    choropleth = fl.Choropleth(
                        geo_data=geojson_path,
                        data=df_choropleth,
                        columns=["bairro", "votos"],
                        key_on="feature.properties.NOME",
                        fill_color='YlGn',
                        nan_fill_color='white',
                        line_opacity=0.7,
                        fill_opacity=0.7,
                        highlight=True,
                        legend_name='Total de Votos'
                    )
                    choropleth.add_to(mapa)
                except Exception as e:
                    print(f"Erro no Choropleth: {e}")
                    # Continuar sem o choropleth se der erro
            
            # Adicionar tooltips
            geojson_data = load_geojson()
            for feature in geojson_data['features']:
                bairro_nome = feature['properties']['NOME']
                votos = votos_dict.get(bairro_nome, 0)
                feature['properties']['tooltip_content'] = f"Bairro: {bairro_nome}<br>Votos: {votos:,}"
            
            # Adicionar GeoJson com tooltip
            fl.GeoJson(
                geojson_data,
                style_function=lambda feature: {
                    'fillColor': 'yellow',
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.1,
                },
                tooltip=fl.GeoJsonTooltip(
                    fields=['tooltip_content'],
                    aliases=[''],
                    localize=True,
                    sticky=False,
                    labels=False,
                    style="background-color: white; color: #333333; font-family: Arial; font-size: 12px; padding: 10px;"
                )
            ).add_to(mapa)
            
            # Converter mapa para HTML
            map_html = mark_safe(mapa._repr_html_())
    
    context = {
        'partidos': partidos,
        'candidatos': candidatos,
        'selected_partido': selected_partido,
        'selected_candidato': selected_candidato,
        'candidato_info': candidato_info,
        'map_html': map_html,
    }
    
    return render(request, 'home.html', context)

def get_candidatos_ajax(request):
    """View AJAX para obter candidatos baseado no partido selecionado"""
    partido = request.GET.get('partido')
    if not partido:
        return JsonResponse({'candidatos': []})
    
    candidatos = list(
        DadoEleitoral.objects
        .filter(sg_partido=partido)
        .values_list('nm_urna_candidato', flat=True)
        .distinct()
        .order_by('nm_urna_candidato')
    )
    
    return JsonResponse({'candidatos': candidatos})