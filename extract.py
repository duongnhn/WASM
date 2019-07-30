#!/usr/bin/env python
"""Utility tools that extracts DWARF information encoded in a wasm output
produced by the LLVM tools, also extracts WASM information then stores them in two seperate files
"""
import argparse
import logging
import sys
import os


def parse_args():
  parser = argparse.ArgumentParser(prog='extract.py', description=__doc__)
  parser.add_argument('input', help='wasm file')
  parser.add_argument('-dwarf-', '--dwarf', help='output dwarf')
  parser.add_argument('-wasm-', '--wasm', help='output wasm')
  return parser.parse_args()


def read_var_uint(wasm, pos):
  n = 0
  shift = 0
  b = ord(wasm[pos:pos + 1])
  pos = pos + 1
  while b >= 128:
    n = n | ((b - 128) << shift)
    b = ord(wasm[pos:pos + 1])
    pos = pos + 1
    shift += 7
  return n + (b << shift), pos


def strip_debug_sections(wasm):
  logging.debug('Strip debug sections')
  print('Strip debug sections')
  code_section_offset = 0
  pos = 8
  stripped = wasm[:pos]
  while pos < len(wasm):
    section_start = pos
    section_id, pos_ = read_var_uint(wasm, pos)
    section_size, section_body = read_var_uint(wasm, pos_)
    pos = section_body + section_size
    if section_id == 0:
      name_len, name_pos = read_var_uint(wasm, section_body)
      name_end = name_pos + name_len
      name = wasm[name_pos:name_end]
      #print(name)
      if name == "linking" or name == "sourceMappingURL" or name.startswith("reloc..debug_") or name.startswith(".debug_"):
        print("skip section ", name)
        continue  # skip debug related sections
    elif section_id == 10: # Code section
      code_section_offset = len(stripped)
    stripped = stripped + wasm[section_start:pos]
  return (stripped, code_section_offset)

def strip_wasm_sections(wasm):
  logging.debug('Strip wasm sections')
  print('Strip wasm sections')
  pos = 8
  stripped = wasm[:pos]
  while pos < len(wasm):
    section_start = pos
    section_id, pos_ = read_var_uint(wasm, pos)
    section_size, section_body = read_var_uint(wasm, pos_)
    pos = section_body + section_size
    if section_id == 0:
      name_len, name_pos = read_var_uint(wasm, section_body)
      name_end = name_pos + name_len
      name = wasm[name_pos:name_end]
      #print(name)
      #if name == "linking" or name == "sourceMappingURL" or name.startswith("reloc..debug_") or name.startswith(".debug_"):
      if name == "linking" or name.startswith("reloc..debug_") or name.startswith(".debug_"):
        print("adding section ", name)
        stripped = stripped + wasm[section_start:pos]
        # skip wasm related sections
  return stripped

def encode_uint_var(n):
  result = bytearray()
  while n > 127:
    result.append(128 | (n & 127))
    n = n >> 7
  result.append(n)
  return bytes(result)

def append_debug_mapping(wasm, url):
  logging.debug('Append debugSymbolsURL section')
  section_name = "sourceMappingURL"
  section_content = encode_uint_var(len(section_name)) + section_name + encode_uint_var(len(url)) + url
  return wasm + encode_uint_var(0) + encode_uint_var(len(section_content)) + section_content

def append_code_section_offset(wasm, code_section_offset):
  logging.debug('Append codeSectionOffset section')
  section_name = "codeSectionOffset"
  section_content = encode_uint_var(len(section_name)) + section_name + encode_uint_var(code_section_offset)
  return wasm + encode_uint_var(0) + encode_uint_var(len(section_content)) + section_content

def main():
  # example: python extract.py fib.wasm --dwarf fib.dwarf --wasm out.wasm

  options = parse_args()
  with open(options.input, 'rb') as infile:
    wasm_input = infile.read()
  with open(options.wasm, 'wb') as outfile_wasm:
    wasm, code_section_offset = strip_debug_sections(wasm_input)
    #print("code_section_offset: ", code_section_offset)
    outfile_wasm.write(append_debug_mapping(wasm, "http://localhost:8889/" + options.dwarf))
  with open(options.dwarf, 'wb') as outfile_dwarf:
    dwarf = strip_wasm_sections(wasm_input)
    outfile_dwarf.write(append_code_section_offset(dwarf, code_section_offset))
  logging.debug('Done')
  return 0
if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG if os.environ.get('EMCC_DEBUG') else logging.INFO)
  sys.exit(main())
