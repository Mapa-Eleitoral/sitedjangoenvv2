# mapa_eleitoral/models.py
from django.db import models

class DadoEleitoral(models.Model):
    """
    Model que mapeia para a tabela eleicao_16_rio existente no MySQL
    """
    # Campo ID adicionado (corresponde à coluna id criada no MySQL)
    id = models.AutoField(primary_key=True)
    
    # Mapeando exatamente os campos da sua tabela MySQL
    ano_eleicao = models.CharField(max_length=4, db_column='ANO_ELEICAO', verbose_name="Ano da Eleição")
    sg_uf = models.CharField(max_length=2, db_column='SG_UF', verbose_name="Código UF")
    nm_ue = models.CharField(max_length=64, db_column='NM_UE', verbose_name="Nome da Unidade Eleitoral")
    ds_cargo = models.CharField(max_length=50, db_column='DS_CARGO', verbose_name="Descrição do Cargo")
    nr_candidato = models.CharField(max_length=8, db_column='NR_CANDIDATO', verbose_name="Número do Candidato")
    nm_candidato = models.CharField(max_length=64, db_column='NM_CANDIDATO', verbose_name="Nome do Candidato")
    nm_urna_candidato = models.CharField(max_length=64, db_column='NM_URNA_CANDIDATO', verbose_name="Nome na Urna")
    nr_cpf_candidato = models.CharField(max_length=11, db_column='NR_CPF_CANDIDATO', verbose_name="CPF do Candidato")
    nr_partido = models.CharField(max_length=100, db_column='NR_PARTIDO', verbose_name="Número do Partido")
    sg_partido = models.CharField(max_length=10, db_column='SG_PARTIDO', verbose_name="Sigla do Partido")
    nr_turno = models.IntegerField(db_column='NR_TURNO', verbose_name="Número do Turno")
    qt_votos = models.DecimalField(max_digits=10, decimal_places=0, db_column='QT_VOTOS', verbose_name="Quantidade de Votos")
    nm_bairro = models.CharField(max_length=100, db_column='NM_BAIRRO', verbose_name="Nome do Bairro")
    nr_latitude = models.CharField(max_length=100, db_column='NR_LATITUDE', verbose_name="Latitude")
    nr_longitude = models.CharField(max_length=100, db_column='NR_LONGITUDE', verbose_name="Longitude")
    
    class Meta:
        db_table = 'eleicao_16_rio'  # Nome da sua tabela MySQL existente
        managed = False  # Django não vai tentar criar/alterar esta tabela
        verbose_name = "Dado Eleitoral"
        verbose_name_plural = "Dados Eleitorais"
    
    def __str__(self):
        return f"{self.nm_urna_candidato} ({self.sg_partido}) - {self.nm_bairro}: {self.qt_votos} votos"