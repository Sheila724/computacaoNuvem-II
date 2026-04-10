#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de inicialização e teste do Projeto Mensageria
Tudo em um único lugar - sem confusão!
"""

import subprocess
import time
import requests
import sys
import os
import json
import threading

class ProjetoMensageria:
    def __init__(self):
        self.db_running = False
        self.api_running = False
        self.api_process = None
        self.base_url = "http://localhost:8000"
        
    def executar_comando(self, comando, descricao):
        """Executa um comando e mostra o resultado"""
        print(f"\n🔄 {descricao}...")
        try:
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            if resultado.returncode == 0:
                print(f"✅ {descricao} - OK")
                return True
            else:
                print(f"❌ {descricao} - ERRO")
                if resultado.stderr:
                    print(f"   Detalhes: {resultado.stderr[:200]}")
                return False
        except Exception as e:
            print(f"❌ {descricao} - EXCEÇÃO: {e}")
            return False
    
    def setup_banco(self):
        """Configura o banco de dados"""
        print("\n" + "="*60)
        print("  1️⃣  INICIANDO BANCO DE DADOS")
        print("="*60)
        
        # Verificar se banco já existe
        cmd_check = 'docker ps | find "postgresql-projeto"'
        resultado = subprocess.run(cmd_check, shell=True, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Banco de dados já está rodando")
            self.db_running = True
            return True
        
        # Iniciar banco
        print("\n1. Criando container Docker...")
        cmd_docker = (
            'docker run -d --name postgresql-projeto '
            '-e POSTGRES_PASSWORD=postgres '
            '-e POSTGRES_DB=mensageria_pubsub '
            '-p 5432:5432 postgres:18'
        )
        
        resultado = subprocess.run(cmd_docker, shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            print(f"❌ Erro ao criar container: {resultado.stderr[:200]}")
            return False
        
        print("✅ Container criado")
        print("⏳ Aguardando banco inicializar...")
        time.sleep(5)
        
        # Criar tabelas
        print("\n2. Criando tabelas...")
        cmd_tabelas = (
            'powershell -Command "Get-Content \'database\\migrations\\001_create_tables.sql\' '
            '| docker exec -i postgresql-projeto psql -U postgres -d mensageria_pubsub"'
        )
        resultado = subprocess.run(cmd_tabelas, shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            print(f"❌ Erro ao criar tabelas: {resultado.stderr[:200]}")
            return False
        print("✅ Tabelas criadas")
        
        # Inserir dados
        print("\n3. Inserindo dados de teste...")
        cmd_dados = (
            'powershell -Command "Get-Content \'database\\seed\\insert_sample_data.sql\' '
            '| docker exec -i postgresql-projeto psql -U postgres -d mensageria_pubsub"'
        )
        resultado = subprocess.run(cmd_dados, shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            print(f"❌ Erro ao inserir dados: {resultado.stderr[:200]}")
            return False
        print("✅ Dados inseridos")
        
        self.db_running = True
        return True
    
    def iniciar_api(self):
        """Inicia a API em background"""
        print("\n" + "="*60)
        print("  2️⃣  INICIANDO API REST (FastAPI)")
        print("="*60)
        
        # Verificar se API já está rodando
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=2)
            print("✅ API já está rodando")
            self.api_running = True
            return True
        except:
            pass
        
        # Iniciar API em background
        print("\n🚀 Iniciando FastAPI na porta 8000...")
        try:
            os.chdir("api-python")
            cmd = "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level critical"
            self.api_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            os.chdir("..")
            
            # Aguardar API iniciar
            print("⏳ Aguardando API iniciar...")
            for i in range(30):
                try:
                    response = requests.get(f"{self.base_url}/docs", timeout=1)
                    if response.status_code == 200:
                        print("✅ API iniciada com sucesso")
                        self.api_running = True
                        return True
                except:
                    time.sleep(1)
            
            print("❌ API não respondeu no tempo esperado")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao iniciar API: {e}")
            return False
    
    def testar_api(self):
        """Testa se a API está respondendo"""
        try:
            response = requests.get(f"{self.base_url}/orders/ORD-2025-0001", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def menu_principal(self):
        """Menu interativo de testes"""
        while True:
            print("\n" + "="*60)
            print("  MENU DE TESTES - PROJETO MENSAGERIA")
            print("="*60)
            print("\n1️⃣  GET um pedido específico")
            print("2️⃣  Listar todos os pedidos")
            print("3️⃣  Filtrar por cliente")
            print("4️⃣  Filtrar por status")
            print("5️⃣  Filtrar por produto")
            print("6️⃣  Testar paginação")
            print("7️⃣  Testar ordenação")
            print("8️⃣  Testar erro 404")
            print("9️⃣  Acessar Documentação (Swagger)")
            print("0️⃣  Sair")
            print("\n" + "-"*60)
            
            opcao = input("Escolha uma opção (0-9): ").strip()
            
            if opcao == "1":
                self.teste_1()
            elif opcao == "2":
                self.teste_2()
            elif opcao == "3":
                self.teste_3()
            elif opcao == "4":
                self.teste_4()
            elif opcao == "5":
                self.teste_5()
            elif opcao == "6":
                self.teste_6()
            elif opcao == "7":
                self.teste_7()
            elif opcao == "8":
                self.teste_8()
            elif opcao == "9":
                self.teste_9()
            elif opcao == "0":
                print("\n👋 Saindo... obrigado por usar!\n")
                break
            else:
                print("❌ Opção inválida!")
            
            input("\n⏎ Pressione ENTER para continuar...")
    
    def teste_1(self):
        """Teste 1: GET um pedido"""
        print("\n📦 Teste 1: GET um pedido específico")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders/ORD-2025-0001"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                print(f"   UUID: {data.get('uuid')}")
                print(f"   Cliente: {data.get('customer', {}).get('name')}")
                print(f"   Total: R$ {data.get('total')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Items: {len(data.get('items', []))}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_2(self):
        """Teste 2: Listar pedidos"""
        print("\n📋 Teste 2: Listar todos os pedidos")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"   Total de pedidos: {pagination.get('totalRecords')}")
                print(f"   Página: {pagination.get('page')} de {pagination.get('totalPages')}")
                print(f"   Items por página: {pagination.get('pageSize')}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_3(self):
        """Teste 3: Filtrar por cliente"""
        print("\n👤 Teste 3: Filtrar por cliente")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders?codigoCliente=7788"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"   Pedidos encontrados: {pagination.get('totalRecords')}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_4(self):
        """Teste 4: Filtrar por status"""
        print("\n⏸️  Teste 4: Filtrar por status")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders?status=separated"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"   Pedidos com status 'separated': {pagination.get('totalRecords')}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_5(self):
        """Teste 5: Filtrar por produto"""
        print("\n🛍️  Teste 5: Filtrar por produto")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders?product_id=9001"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"   Pedidos com este produto: {pagination.get('totalRecords')}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_6(self):
        """Teste 6: Paginação"""
        print("\n📄 Teste 6: Testar paginação")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders?page=1&pageSize=5"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"   Página: {pagination.get('page')}")
                print(f"   Items por página: {pagination.get('pageSize')}")
                print(f"   Total de páginas: {pagination.get('totalPages')}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_7(self):
        """Teste 7: Ordenação"""
        print("\n↕️  Teste 7: Testar ordenação")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders?sortBy=created_at&sortOrder=desc"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Sucesso!")
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"   Ordenação: {pagination.get('sortBy')} ({pagination.get('sortOrder')})")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_8(self):
        """Teste 8: Erro 404"""
        print("\n⚠️  Teste 8: Testar erro 404")
        print("-" * 60)
        try:
            url = f"{self.base_url}/orders/NAO-EXISTE"
            print(f"URL: {url}\n")
            response = requests.get(url, timeout=5)
            if response.status_code == 404:
                print("✅ Sucesso! (Erro 404 retornado corretamente)")
                print(f"   Mensagem: {response.json().get('error')}")
            else:
                print(f"❌ Erro inesperado: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def teste_9(self):
        """Teste 9: Documentação"""
        print("\n📚 Teste 9: Documentação Swagger")
        print("-" * 60)
        print(f"\n🔗 URL da Documentação:")
        print(f"   http://localhost:8000/docs")
        print(f"\n💡 Abra esta URL no seu navegador para ver:")
        print(f"   - Todos os endpoints disponíveis")
        print(f"   - Parâmetros de cada endpoint")
        print(f"   - Exemplos de requisições")
        print(f"   - Testar a API diretamente")
    
    def executar(self):
        """Executa o programa"""
        print("="*60)
        print("  PROJETO MENSAGERIA - Setup e Testes")
        print("="*60)
        
        # Setup banco
        if not self.setup_banco():
            print("\n❌ Erro ao configurar banco de dados!")
            return
        
        # Iniciar API
        if not self.iniciar_api():
            print("\n❌ Erro ao iniciar API!")
            return
        
        # Menu
        print("\n" + "="*60)
        print("  ✅ TUDO PRONTO!")
        print("="*60)
        print("  Banco: http://localhost:5432")
        print("  API: http://localhost:8000")
        print("  Docs: http://localhost:8000/docs")
        print("="*60)
        
        self.menu_principal()

if __name__ == "__main__":
    app = ProjetoMensageria()
    app.executar()
