#!/usr/bin/env python3
"""
Script de prueba para validar las correcciones específicas del MANDATO 5/X FASES 2 Y 3
Casos específicos del usuario:
1. "Banco Mercantil, C . A . S . A . C . A, Banco Universal" → "BANCO MERCANTIL"
2. "0412 *** 244" → Teléfono con máscara de seguridad válido
3. "20/06/ 2025" → Fecha con espacio adicional manejada correctamente
4. "210,00" → Monto venezolano normalizado a "210.00"
"""

import sys
sys.path.append('.')

from main_ocr_process import OrquestadorOCR
import json

def test_correcciones_mandato_5x():
    """
    Prueba las correcciones específicas implementadas para el Mandato 5/X Fases 2 y 3
    """
    print("🔍 INICIANDO PRUEBAS DE CORRECCIONES ESPECÍFICAS MANDATO 5/X FASES 2 Y 3")
    print("=" * 80)
    
    # Texto de prueba con los casos específicos mencionados por el usuario
    texto_prueba = """
    A Personas 104,54 Bs Fecha : 20/06/ 2025 Operacion; 003039387344
    Concepto Nro . Referencia Fecha y hora 106 93 48311146148
    Banco Mercantil, C . A . S . A . C . A, Banco Universal
    Telefono: 0412 *** 244
    Monto: 210,00 Bs
    """
    
    orquestador = OrquestadorOCR()
    
    # Simular extracted_fields vacío para probar las correcciones
    extracted_fields = {}
    
    print(f"📝 TEXTO DE PRUEBA:\n{texto_prueba}")
    print("\n" + "=" * 80)
    
    # Aplicar correcciones específicas
    print("🔧 APLICANDO CORRECCIONES ESPECÍFICAS...")
    corrected_fields = orquestador._aplicar_correcciones_mandato_5x_fases_2_3(
        extracted_fields, texto_prueba
    )
    
    print("\n✅ RESULTADOS DE LAS CORRECCIONES:")
    print("=" * 80)
    
    for campo, valor in corrected_fields.items():
        if valor:
            print(f"📋 {campo}: '{valor}'")
    
    print("\n🎯 VALIDACIÓN DE CASOS ESPECÍFICOS:")
    print("=" * 80)
    
    # Validar caso 1: Banco Mercantil
    if corrected_fields.get('banco_destino') == 'BANCO MERCANTIL':
        print("✅ CASO 1: 'Banco Mercantil, C . A . S . A . C . A, Banco Universal' → 'BANCO MERCANTIL' ✓")
    else:
        print("❌ CASO 1: Banco destino no detectado correctamente")
    
    # Validar caso 2: Teléfono con máscara
    if corrected_fields.get('telefono') == '0412***244':
        print("✅ CASO 2: '0412 *** 244' → Teléfono con máscara válido ✓")
    else:
        print("❌ CASO 2: Teléfono con máscara no detectado correctamente")
    
    # Validar caso 3: Fecha con espacio
    if corrected_fields.get('pago_fecha') == '20/06/ 2025':
        print("✅ CASO 3: '20/06/ 2025' → Fecha con espacio manejada correctamente ✓")
    else:
        print("❌ CASO 3: Fecha con espacio no detectada correctamente")
    
    # Validar caso 4: Monto venezolano
    if corrected_fields.get('monto') == '210.00':
        print("✅ CASO 4: '210,00' → '210.00' (monto normalizado) ✓")
    else:
        print("❌ CASO 4: Monto venezolano no normalizado correctamente")
    
    print("\n🏆 PRUEBA COMPLETADA")
    print("=" * 80)
    
    return corrected_fields

if __name__ == "__main__":
    test_correcciones_mandato_5x()