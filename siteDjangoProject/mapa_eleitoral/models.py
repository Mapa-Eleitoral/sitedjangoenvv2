# mapa_eleitoral/models.py
from django.db import models

class DadoEleitoral(models.Model):
    # Campos baseados no que você tinha no parquet
    sg_partido = models.CharField(max_length=20, verbose_name="Sigla do Partido")
    nm_urna_candidato = models.CharField(max_length=200, verbose_name="Nome do Candidato")
    ds_cargo = models.CharField(max_length=100, verbose_name="Cargo")
    nm_bairro = models.CharField(max_length=200, verbose_name="Nome do Bairro")
    qt_votos = models.IntegerField(default=0, verbose_name="Quantidade de Votos")
    
    # Campos adicionais que podem ser úteis
    ano_eleicao = models.IntegerField(default=2016, verbose_name="Ano da Eleição")
    nm_municipio = models.CharField(max_length=200, default="RIO DE JANEIRO", verbose_name="Município")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dados_eleitorais'  # Nome da tabela no MySQL
        verbose_name = "Dado Eleitoral"
        verbose_name_plural = "Dados Eleitorais"
        indexes = [
            models.Index(fields=['sg_partido']),
            models.Index(fields=['nm_urna_candidato']),
            models.Index(fields=['nm_bairro']),
            models.Index(fields=['sg_partido', 'nm_urna_candidato']),
        ]
    
    def __str__(self):
        return f"{self.nm_urna_candidato} ({self.sg_partido}) - {self.nm_bairro}: {self.qt_votos} votos"

# Model alternativo se você quiser usar uma view ou tabela existente
class DadoEleitoralRaw(models.Model):
    """
    Use este model se você já tem uma tabela MySQL 
    e quer mapear diretamente para ela
    """
    # Mapeie os campos exatamente como estão no seu MySQL
    partido = models.CharField(max_length=20, db_column='SG_PARTIDO')
    candidato = models.CharField(max_length=200, db_column='NM_URNA_CANDIDATO')
    cargo = models.CharField(max_length=100, db_column='DS_CARGO')
    bairro = models.CharField(max_length=200, db_column='NM_BAIRRO')
    votos = models.IntegerField(db_column='QT_VOTOS')
    
    class Meta:
        db_table = 'sua_tabela_mysql_existente'  # Nome da sua tabela real
        managed = False  # Django não vai gerenciar esta tabela
        verbose_name = "Dado Eleitoral Raw"