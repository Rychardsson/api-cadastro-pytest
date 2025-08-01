#!/usr/bin/env python3
"""
Script para executar testes com diferentes configurações.
"""

import subprocess
import sys
import argparse

def run_command(cmd, description):
    """Executa um comando e exibe o resultado."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Script de testes para API de Cadastro")
    parser.add_argument("--all", action="store_true", 
                       help="Executa todos os tipos de testes")
    parser.add_argument("--unit", action="store_true", 
                       help="Executa apenas testes unitários")
    parser.add_argument("--integration", action="store_true", 
                       help="Executa apenas testes de integração")
    parser.add_argument("--performance", action="store_true", 
                       help="Executa apenas testes de performance")
    parser.add_argument("--coverage", action="store_true", 
                       help="Executa testes com cobertura de código")
    parser.add_argument("--verbose", action="store_true", 
                       help="Executa com saída verbosa")
    
    args = parser.parse_args()
    
    # Comandos base
    base_cmd = "python -m pytest tests/"
    verbose_flag = " -v" if args.verbose else ""
    
    commands = []
    
    if args.all or (not any([args.unit, args.integration, args.performance, args.coverage])):
        commands.append((
            f"{base_cmd}{verbose_flag}",
            "Executando todos os testes"
        ))
    
    if args.unit:
        commands.append((
            f"{base_cmd} -m 'not integration and not performance'{verbose_flag}",
            "Executando testes unitários"
        ))
    
    if args.integration:
        commands.append((
            f"{base_cmd} -m integration{verbose_flag}",
            "Executando testes de integração"
        ))
    
    if args.performance:
        commands.append((
            f"{base_cmd} -m performance{verbose_flag}",
            "Executando testes de performance"
        ))
    
    if args.coverage:
        commands.append((
            f"python -m pytest tests/ --cov=. --cov-report=html --cov-report=term{verbose_flag}",
            "Executando testes com cobertura de código"
        ))
    
    # Executa os comandos
    success_count = 0
    for cmd, description in commands:
        if run_command(cmd, description):
            success_count += 1
    
    # Resumo final
    print(f"\n{'='*60}")
    print(f"📊 RESUMO: {success_count}/{len(commands)} comandos executados com sucesso")
    print(f"{'='*60}")
    
    if success_count == len(commands):
        print("✅ Todos os testes passaram!")
        return 0
    else:
        print("❌ Alguns testes falharam!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
