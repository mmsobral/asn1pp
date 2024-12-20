import sys,os
import ply.yacc as yacc
import ply.lex as lex
import traceback
from asn1 import *

class SemanticError(Exception):

  def __init__(self, lineno, value, line=''):
    self.value = value
    self.n = lineno
    self.line = line

  def __str__(self):
      return 'Semantic error: %s' % self.value

class ParseError (Exception):

  def __init__(self, lineno, column, value, line=''):
    self.column = column
    self.value = value
    self.line = line
    self.n = lineno

  def __str__(self):
    if self.column < 0:
      return 'Parse error: %s' % self.value
    else:
      return 'Parse error at line %d, column %d: %s' % (self.n, self.column, self.value)

### Gerador de codigo
class ASN1Builder:

  def __init__(self, modules):
    self.modules = {}
    for module in modules:
      self.modules[module.name] = module
          
  # gera uma lista de nomes de modulos por ordem de dependencia
  def __modules__(self):
    l = self.modules.values()
    r = []
    while l:
      nl = []
      for m in l:
        ok = True
        for ext in m.external:
          if not ext in r:
            ok = False
            break
        if ok:
          r.append(m.name)
        else:
          nl.append(m)
      if len(l) == len(nl):
        raise ValueError('dependencias entre modulos nao pode ser resolvida ... talvez uma dependencia circular ???: len(nl)=%d, names=%s, r=%s, modules=%s' % (len(nl), map(lambda x: x.name, nl), map(lambda x: x.name, r), self.modules.keys()))
      l = nl
    return r
    
  def build(self, path='.'):
    try:
      os.mkdir(path)
    except:
      pass
    arqs = []
    for name in self.__modules__():
      module = self.modules[name]
      code = module.gen_header(self.modules)
      arq = '%s/parser_%s.h' % (path, name)
      arqs.append(arq)
      open(arq, 'w').write(code)
    return arqs

### Parser ASN1
class ASN1Parser:

  start = 'statement'
  t_ignore = ' \t'
  precedence = ()
  literals = ''

  t_DOT = r'\.'
  t_LBRACE = r'\{'
  t_RBRACE = r'\}'
  t_EQUALS  = r'::='
  t_LPAR = r'\('
  t_RPAR = r'\)'
  t_NUMBER = r'\d+'
  t_VIRG = r','
  t_HCOMMA = r';'
  reserved = {'OBJECT':'OBJECT', 'IDENTIFIER':'IDENTIFIER', 'RELATIVE-OID':'ROID',
              'STRING':'STRING', 'BOOLEAN':'BOOLEAN',
              'BIT':'BIT','SET':'SET', 'SEQUENCE':'SEQUENCE','OF':'OF','OPTIONAL':'OPTIONAL',
              'OCTET':'OCTET', 'DEFINITIONS':'DEFINITIONS','AUTOMATIC':'AUTOMATIC',
              'TAGS':'TAGS','BEGIN':'BEGIN', 'END':'END', 'SIZE':'SIZE',
              'MIN':'MIN', 'MAX':'MAX', 'INTEGER':'INTEGER', 'ENUMERATED':'ENUMERATED',
              'CHOICE':'CHOICE', 'IMPORTS':'IMPORTS','FROM':'FROM',
              'EXPORTS':'EXPORTS', 'UTCTime':'UTCTIME', 'NULL':'NULL'}

  tokens = (
    'DOT', 'EQUALS','NUMBER', 'LBRACE','RBRACE',
    'LPAR','RPAR','COMMENT','TSTRING','ID',
    'VIRG', 'HCOMMA')


  def __init__(self, confs):
    self.tokens += tuple(self.reserved.values())
    if type(confs) == type(''): confs = [confs]
    if not type(confs) in [type([]), type(())]:
      raise ValueError('Arquivos a serem analisados devem ser fornecidos como lista u tupla')
    self.confs = confs # lista de arquivos
    self.__built = False
    self.external = {}
    self.modules = []
    self.exports = []

  def build(self, **args):
    self.lex = lex.lex(module=self, **args)
    self.yacc = yacc.yacc(module=self)
    self.__built = True

  def get_reserved(self, token):
    it = self.reserved.iteritems()
    while True:
      try:
        key,val = it.next()
        if val == token: return key
      except StopIteration:
        return None

  def t_TSTRING(self, t):
    r'NumericString|VisibleString|IA5String|PrintableString'
    return t

  def t_ID(self, t):
    r'[a-zA-Z_][-a-zA-Z_0-9]*'
    t.type = self.reserved.get(t.value,'ID')    # Check for reserved words
    return t

  def t_COMMENT(self, t):
    r'--.*'
    pass

  def t_newline(self, t):
    r'\n+'
    self.lex.lineno += len(t.value)
    
  def t_error(self, t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

  def __parse__(self, conf):
    if not self.__built: self.build()
    self.lex.lineno = 0
    f=open(conf)
    r = []
    buffer = f.read()
    try:
      r = self.yacc.parse(buffer, lexer=self.lex)
      #print self.lex.lineno
    except SyntaxError:
      pass
    f.close()
    if not r:
      raise SyntaxError('nada reconhecido ...')

  def parse(self):
    for conf in self.confs:
      self.__parse__(conf)
    
  def get_builder(self):
    return ASN1Builder(self.modules)
    
  def p_error(self,p):
    if not p:
      raise SyntaxError("Unknown or incomplete declaration")
    raise ParseError(self.lex.lineno, p.lexpos, p.value)

  def tokenize(self, x=''):
    lexer = lex.lex(module=self)
    lexer.input(x)
    #print self.tokens, tokens, t_ID
    r = []
    while True:
      tok = lexer.token()
      if not tok: break
      r.append(tok)
    return r

  def p_statement_module1(self, p):
    'statement : ID DEFINITIONS EQUALS BEGIN structs END'
    m = Module(p[1])
    m.add_members(p[5])
    m.set_exportable(self.exports)
    self.modules.append(m)
    p[0] = p[5]

  def p_statement_module2(self, p):
    '''statement : ID DEFINITIONS AUTOMATIC TAGS EQUALS BEGIN structs END '''
    m = Module(p[1])
    m.add_members(p[7])
    m.set_exportable(self.exports)
    self.modules.append(m)
    #print '-->>>', p[1], p[7]
    p[0] = p[7]

  def p_statement_module3(self, p):
    '''statement : ID LBRACE arcs RBRACE DEFINITIONS AUTOMATIC TAGS EQUALS BEGIN structs END '''
    #print p[3]
    m = Module(p[1])
    m.add_members(p[10])
    m.set_exportable(self.exports)
    self.modules.append(m)
    p[0] = p[10]

  def p_arcs_decl1(self, p):
    r'arcs : arc arcs'
    p[0] = [p[1]]
    p[0] += p[2]

  def p_arcs_decl2(self, p):
    r'arcs : arc'
    p[0] = [p[1]]

  def p_arc_decl1(self, p):
    r'arc : ID'
    p[0] = (p[1], -1)

  def p_arc_decl2(self, p):
    r'arc : ID LPAR NUMBER RPAR'
    p[0] = (p[1], int(p[3]))

  def p_arc_decl3(self, p):
    r'arc : NUMBER'
    p[0] = ('', int(p[1]))

  def p_structs_decl1(self, p):
    r'structs : struct'
    if isinstance(p[1], list):
      p[0] = p[1]
    else:
      p[0] = [p[1]]

  def p_structs_decl2(self, p):
    r'structs : struct structs'
    if isinstance(p[1], list):
      p[2] += p[1]
    else:
      p[2].append(p[1])
    p[0] = p[2]

  def p_structs_decl3(self, p):
    r'structs : COMMENT'

  def p_idlist_decl1(self, p):
    r'idlist : ID'
    p[0] = [p[1]]

  def p_idlist_decl2(self, p):
    r'idlist : ID VIRG idlist'
    p[3].append(p[1])
    p[0] = p[3]

  def p_struct_decl1(self, p):
    'struct : ID EQUALS sequence'
    p[3].set_name(p[1])
    p[0] = p[3]

  def p_struct_decl2(self, p):
    'struct : ID EQUALS enumerated'
    p[0] = Enum(p[1])
    #p[0].set_name(p[1])
    #p[0].set_fields(p[3])

  def p_struct_decl3(self, p):
    '''struct : ID EQUALS type
              | ID EQUALS type extra'''
    p[0] = p[3]
    p[3].embed = False
    p[0].set_name(p[1])

  def p_struct_decl4(self, p):
    r'struct : IMPORTS imports HCOMMA'
    p[0] = p[2]

  def p_struct_decl5(self, p):
    r'struct : EXPORTS idlist HCOMMA'
    self.exports += p[2]
    p[0] = []    

  def p_struct_decl6(self, p):
    'struct : ID EQUALS set'
    p[3].set_name(p[1])
    p[0] = p[3]

  def p_imports_decl1(self, p):
    r'imports : import  imports'
    p[2] += p[1]
    p[0] = p[2]

  def p_imports_decl2(self, p):
    r'imports : import'
    p[0] = p[1]

  def p_import_decl1(self, p):
    r'import : idlist FROM ID'
    r = []
    for name in p[1]:
      r.append(StubType(name, p[3]))
      #print 'imports:', name, p[4], 'mod=%s'%r[-1].module
    p[0] = r
    
  def p_sequence_decl1(self, p):
    'sequence : SEQUENCE LBRACE fields RBRACE'
    p[0] = Sequence()
    p[0].set_fields(p[3])
    
  def p_set_decl1(self, p):
    'set : SET LBRACE fields RBRACE'
    p[0] = Set()
    p[0].set_fields(p[3])

  def p_enumerated_decl1(self, p):
    'enumerated : ENUMERATED LBRACE emembers RBRACE'
    p[0] = p[3]

  def p_emembers_decl1(self, p):
    r'emembers : emember VIRG emembers'
    p[3].append(p[1])
    p[0] = p[3]

  def p_emembers_decl2(self, p):
    r'emembers : emember'
    p[0] = [p[1]]

  def p_emember_decl1(self, p):
    r'''emember : ID
                | ID LPAR NUMBER RPAR'''
    p[0] = [p[1]]

  def p_fields_decl1(self, p):
    r'''fields : member VIRG fields'''
    p[3].update(p[1])
    p[0] = p[3]

  def p_fields_decl2(self, p):
    r'''fields : member'''
    p[0] = p[1]

  def p_member_decl1(self, p):
    r'''member : ID type
               | ID type extra'''
    if isinstance(p[2], Choice): p[2].set_name(p[1])
    elif isinstance(p[2], BitString): 
      if len(p) > 3: p[2].set_size(p[3])
    p[0] = {p[1]:p[2]}

  def p_member_decl2(self, p):
    r'''member : ID sequence
               | ID sequence extra
               | ID set
               | ID set extra'''
    print ('anon. sequence:', p[1])
    p[2].set_name(p[1])
    p[0] = {p[1]:p[2]}

  def p_member_decl3(self, p):
    r'''member : ID enumerated
               | ID enumerated extra'''
    print ('anon. enumerated:', p[1])
    p[0] = Enumerated(p[1])

  def p_extra_decl1(self, p):
    r'''extra : size
              | size OPTIONAL
              | OPTIONAL'''
    p[0] = p[1]

  def p_size_decl1(self, p):
    r'size : LPAR SIZE LPAR NUMBER RPAR RPAR'
    p[0] = (int(p[4]), int(p[4]))
              
  def p_size_decl2(self, p):
    r'''size : LPAR SIZE LPAR NUMBER DOT DOT NUMBER RPAR RPAR'''
    n = int(p[4])
    p[0] = (n, n)
              
  def p_type_decl1(self, p):
    r'type : TSTRING'
    p[0] = String()

  def p_type_decl2(self, p):
    r'type : OCTET STRING'
    p[0] = String()
    
  def p_type_decl3(self, p):
    r'type : BIT STRING'
    p[0] = BitString()

  def p_type_decl4(self, p):
    r'''type : INTEGER
             | INTEGER range'''
    p[0] = Integer()

  def p_range_decl1(self, p):
    r'''range : LPAR NUMBER DOT DOT NUMBER RPAR
              | LPAR MIN DOT DOT NUMBER RPAR
              | LPAR NUMBER DOT DOT MAX RPAR
              | LPAR MIN DOT DOT MAX RPAR'''

  def p_type_decl5(self, p):
    r'type : BOOLEAN'
    p[0] = Boolean()

  def p_type_decl6(self, p):
    r'''type : SET OF type
             | SEQUENCE OF type'''
    obj = p[3]
    p[0] = List(obj)

  def p_type_decl7(self, p):
    r'type : OBJECT IDENTIFIER'
    p[0] = Oid()

  def p_type_decl8(self, p):
    r'type : ROID'
    p[0] = Roid()

  def p_type_decl9(self, p):
    r'type : CHOICE LBRACE fields RBRACE'
    p[0] = Choice()
    p[0].set_fields(p[3])

  def p_type_decl10(self, p):
    r'type : ID'
    p[0] = StubType(p[1])

  def p_type_decl11(self, p):
    r'''type : NULL'''
    p[0] = Null()

  def p_type_decl12(self, p):
    r'''type : UTCTIME'''
    p[0] = UTCTime()

