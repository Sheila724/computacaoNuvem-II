#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para executar o Consumer Pub/Sub
Recebe mensagens do professor e persiste no banco
"""

import subprocess
import os
import sys
import time

def executar_comando(comando, descricao):
    """Executa um comando"""
    print(f"\n🔄 {descricao}...")
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            cwd="consumer-js"
        )
        return resultado.returncode == 0
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("="*70)
    print("  CONSUMER PUB/SUB - Receber Mensagens do Professor")
    print("="*70)
    
    # Verificar se service-account-key.json existe
    if not os.path.exists("consumer-js/service-account-key.json"):
        print("\n❌ ERRO: Arquivo 'service-account-key.json' não encontrado!")
        print("\n📝 O que fazer:")
        print("   1. Copie o arquivo service-account-key.json que o professor deu")
        print("   2. Cole em: consumer-js/service-account-key.json")
        print("   3. Execute este script novamente")
        return
    
    print("✅ Arquivo de credenciais encontrado")
    
    # Verificar/instalar dependências
    if not os.path.exists("consumer-js/node_modules"):
        print("\n📦 Instalando dependências (primeira execução)...")
        if not executar_comando("npm install", "Instalando pacotes Node.js"):
            print("❌ Erro ao instalar dependências")
            return
    else:
        print("✅ Dependências já instaladas")
    
    # Iniciar consumer
    print("\n" + "="*70)
    print("  🚀 INICIANDO CONSUMER")
    print("="*70)
    print("\n📢 Aguardando mensagens do Pub/Sub...")
    print("   (Quando o professor enviar, você verá aqui)")
    print("\n💡 Dica: Pressione CTRL+C para parar\n")
    
    executar_comando("npm start", "Iniciando consumer")

if __name__ == "__main__":
    main()
