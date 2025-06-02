from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import json
import os
from django.conf import settings
import folium as fl
from folium.features import GeoJsonTooltip
from functools import lru_cache
import gc
from django.utils.safestring import mark_safe

@lru_cache(maxsize=1)
def load_data():
    """Carregar dados do parquet"""
    parquet_path = os.path.join(settings.BASE_DIR, 'mapa_eleitoral', 'data', 'eleicao_16_rio.parquet')
    df = pd.read_parquet(parquet_path)
    df['QT_VOTOS'] = pd.to_numeric(df['QT_VOTOS'], errors='coerce').fillna(0).astype(int)
    return df

@lru_cache(maxsize=1)
def load_geojson():
    """Carregar dados do GeoJSON"""
    geojson_path = os.path.join(settings.BASE_DIR, 'mapa_eleitoral', 'data', 'Limite_Bairro.geojson')
    with open(geojson_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def home_view(request):
    """View principal do mapa eleitoral"""
    df = load_data()
    
    # Obter lista de partidos
    partidos = sorted(df["SG_PARTIDO"].dropna().unique())
    
    # Partido e candidato selecionados (via GET parameters)
    selected_partido = request.GET.get('partido', 'PRB')
    selected_candidato = request.GET.get('candidato', '')
    
    # Filtrar por partido
    sel_part = df[df["SG_PARTIDO"] == selected_partido]
    candidatos = sorted(sel_part["NM_URNA_CANDIDATO"].dropna().unique()) if not sel_part.empty else []
    
    # Se não há candidato selecionado, usar o primeiro ou o padrão
    if not selected_candidato or selected_candidato not in candidatos:
        selected_candidato = 'CRIVELLA' if 'CRIVELLA' in candidatos else (candidatos[0] if candidatos else '')
    
    # Dados do mapa
    map_html = ""
    candidato_info = {}
    
    if selected_candidato:
        # Filtrar dados do candidato
        cand_data = sel_part[sel_part["NM_URNA_CANDIDATO"] == selected_candidato]
        
        if not cand_data.empty:
            # Calcular votos por bairro
            votos_por_bairro = cand_data.groupby('NM_BAIRRO')['QT_VOTOS'].sum().reset_index()
            votos_dict = dict(zip(votos_por_bairro['NM_BAIRRO'], votos_por_bairro['QT_VOTOS']))
            
            # Informações do candidato
            cand_stats = cand_data.iloc[0]
            candidato_info = {
                'nome': cand_stats['NM_URNA_CANDIDATO'],
                'cargo': cand_stats['DS_CARGO'],
                'votos_total': cand_data['QT_VOTOS'].sum()
            }
            
            # Criar mapa com configurações específicas para Django
            mapa = fl.Map(
                location=[-22.928777, -43.423878], 
                zoom_start=10, 
                tiles='CartoDB positron',
                # Adicionar configurações para evitar problemas de segurança
                prefer_canvas=True
            )
            
            # Caminho do GeoJSON
            geojson_path = os.path.join(settings.BASE_DIR, 'mapa_eleitoral', 'data', 'Limite_Bairro.geojson')
            
            # Adicionar Choropleth
            choropleth = fl.Choropleth(
                geo_data=geojson_path,
                data=cand_data,
                columns=["NM_BAIRRO", "QT_VOTOS"],
                key_on="feature.properties.NOME",
                fill_color='YlGn',
                nan_fill_color='white',
                line_opacity=0.7,
                fill_opacity=0.7,
                highlight=True,
                legend_name='Total de Votos'
            )
            choropleth.add_to(mapa)
            
            # Carregar GeoJSON e adicionar tooltips
            geojson_data = load_geojson()
            for feature in geojson_data['features']:
                bairro_nome = feature['properties']['NOME']
                votos = votos_dict.get(bairro_nome, 0)
                feature['properties']['tooltip_content'] = f"Bairro: {bairro_nome}<br>Votos: {votos}"
            
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
            
            # Converter mapa para HTML e marcar como seguro
            map_html = mark_safe(mapa._repr_html_())
    
    context = {
        'partidos': partidos,
        'candidatos': candidatos,
        'selected_partido': selected_partido,
        'selected_candidato': selected_candidato,
        'candidato_info': candidato_info,
        'map_html': map_html,
    }
    
    gc.collect()
    return render(request, 'home.html', context)

def get_candidatos_ajax(request):
    """View AJAX para obter candidatos baseado no partido selecionado"""
    partido = request.GET.get('partido')
    if not partido:
        return JsonResponse({'candidatos': []})
    
    df = load_data()
    sel_part = df[df["SG_PARTIDO"] == partido]
    candidatos = sorted(sel_part["NM_URNA_CANDIDATO"].dropna().unique())
    
    gc.collect()
    return JsonResponse({'candidatos': candidatos})