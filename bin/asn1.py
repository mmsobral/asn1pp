# representa um membro de um SEQUENCE ou CHOICE
#
# atributos:
# name: nome da variavel/membro
# classname: classe de acordo com a API ASN1++
# typename: tipo ou classe C++ encapsulado pela "classname" da API
# Obs: se typename for um tipo basico, como INTEGER ou BOOLEAN, entao
# classname = typename
#
# operacoes:
# get_code(): gera getter e setter
# get_constructor_code(): gera sentencas a inserir no constructor do parser
# get_destructor_code(): gera sentencas a inserir no destructor do parser
# get_var_code(): gera sentencas para obter valor do tipo "typename"
# get_setvar_code(): gera sentencas para modificar do tipo "typename"

class Type:

  # classe ASN1++
  classname = ''
  # Tipo de dados exportado/importado
  typename = ''

  def __init__(self):
    self.name = ''
    self.exportable = False
    self.module = ''

  def set_name(self, name):
    self.name = name

  def set_module(self, name):
    self.module = name

  def set_exportable(self):
    self.exportable = True

  def get_asntype(self):
    if self.name: return '%s_t' % self.name
    return self.typename

  def __eq__(self, o):
    return self.typename == o.typename and self.classname == o.classname

  def __neq__(self, o):
    return not self == o

  def __repr__(self):
    return '%s,%s' % (self.typename, self.classname)

  def check_types(self, modules):
    pass

  def get_data(self, var):
    return var

  def get_instance(self, var):
    return var

  def get_member(self, member):
    return self

  def get_header_code(self, sep=''):
    if self.name: return '%s#include<%s.h>\n' % (sep, self.name)
    return ''

  def gen_code(self, sep=''):
    return ''

  def get_getter(self, name, sep=''):
    r = '%s  %s & get_%s() { return *m_%s;}\n' % (sep, self.typename, name, name)
    return r

  def get_setter(self, name, sep=''):
    r = '%s  void set_%s(const %s & arg) { *m_%s = arg;}\n' % (sep, name, self.typename, name)
    return r

  def get_constructor_code(self, name, sep=''):
    r = '%s    m_%s = new %s(pkt->%s);\n' % (sep, name, self.classname, name)
    return r

  def get_destructor_code(self, name, sep=''):
    r = '%s    delete m_%s;\n' % (sep, name)
    return r

  def get_var_code(self, name, prefix, sep=''):
    return ''

  def get_setvar_code(self, name, prefix, arg, sep=''):
    return ''

  def get_var_decl(self, name, sep=''):
    r = '%s  %s * m_%s;\n' % (sep, self.classname, name)
    return r

  def dependencies(self):
    return []

class BasicType(Type):

  def get_getter(self, name, sep=''):
    r = '%s  %s get_%s() { return pkt->%s;}\n' % (sep, self.typename, name, name)
    return r

  def get_setter(self, name, sep=''):
    r = '%s  void set_%s(%s arg) { pkt->%s = arg;}\n' % (sep, name, self.typename, name)
    return r

  def get_constructor_code(self, name, sep=''):
    return ''

  def get_destructor_code(self, name, sep=''):
    return ''

  def get_var_code(self, name, prefix, sep=''):
    r = '%s    %s & pld = %s%s;\n' % (sep, self.typename, prefix, name)
    return r

  def get_setvar_code(self, name, prefix, arg, sep=''):
    r = '%s%s%s = %s;\n' % (sep, prefix, name, arg)
    return r

  def get_var_decl(self, name, sep=''):
    return ''

class Enumerated(BasicType):

  def __init__(self, name):
    BasicType.__init__(self)
    self.classname = '%s_t' % name
    self.typename = '%s_t' % name
    self.native = self.typename

  def set_fields(self, fields):
    self.fields = fields

class String(Type):

  classname = 'ASN1String'
  typename = 'string'
  native = 'OCTET_STRING_t'

  def get_instance(self, var):
    return 'ASN1String(%s).str()' % var

  def get_data(self, var):
    return 'ASN1String(%s)._get_data()' % var

  #def get_instance(self, var):
  #  return '%s(%s)' % (self.classname, var)

  def get_getter(self, name, sep=''):
    r = '%s  %s get_%s() { return m_%s->str();}\n' % (sep, self.typename, name, name)
    return r

  def get_setter(self, name, sep=''):
    r = '%s  void set_%s(const %s & arg) { *m_%s = arg;}\n' % (sep, name, self.typename, name)
    return r

  def get_var_code(self, name, prefix='msg->', sep=''):
    r = '%s    %s f_%s(%s%s);\n' % (sep, self.classname, name, prefix, name)
    r += '%s    %s pld = f_%s.str();\n' % (sep, self.typename, name)
    return r

  def get_setvar_code(self, name, prefix, arg, sep=''):
    r = '%sASN1String attr(%s%s);\n' % (sep, prefix, name)
    r += '%sattr = %s;\n' % (sep, arg)
    return r

class UTCTime(Type):

  classname = 'ASN1Utime'
  typename = 'time_t'
  native = 'UTCTime_t'

  def get_getter(self, name, sep=''):
    #r = '%s  %s get_%s() { return asn_UT2time(m_%s->str().c_str(), NULL, 0);}\n'
    r = '%s  %s get_%s() { return m_%s->get_time();}\n' % (sep, self.typename, name, name)
    return r

  def get_setter(self, name, sep=''):
    r = '%s  void set_%s(const %s & arg) { \n' % (sep, name, self.typename)
    r += '%s    *m_%s = arg;\n' % (sep, name)
    #r += '%s    struct tm * now = localtime(&arg);\n' % sep
    #r += '%s    UTCTime_t * ut = asn_time2UT(NULL, now, 0);\n' % sep
    #r += '%s    *m_%s = *ut;\n' % (sep, name)
    #r += '%s    delete ut;\n' % sep
    r += '%s  }\n' % sep
    return r

  def get_var_code(self, name, prefix='msg->', sep=''):
    r = '%s    %s f_%s(%s%s);\n' % (sep, self.classname, name, prefix, name)
    #r += '%s    %s pld = asn_UT2time(f_%s->str().c_str(), NULL, 0);\n'
    r += '%s    %s pld = f_%s->get_time();\n' % (sep, self.typename, name)
    return r

  def get_setvar_code(self, name, prefix, arg, sep=''):
    r = '%sASN1Utime attr(%s%s);\n' % (sep, prefix, name)
    r += '%sattr = %s;\n' % (sep, arg)
    #r = '%sASN1String attr(%s%s);\n' % (sep, prefix, name)
    #r += '%sstruct tm * now = localtime(&%s);\n' % (sep, arg)
    #r += '%sUTCTime_t * ut = asn_time2UT(NULL, now, 0);\n' % sep
    #r += '%sattr = *ut;\n' % sep
    #r += '%sdelete ut;\n' % sep
    return r

  def get_instance(self, var):
    #return 'asn_UT2time(ASN1String(%s).str().c_str(), NULL, 0)' % var
    return 'ASN1Utime(%s).get_time()' % var

  # isto causa mem. leak ... asn_time2UT aloca memoria, que deve ser liberada !
  # talvez uma forma facil de resolver seja especializar ASN1String para
  # uma nova classe ASN1Utime ...
  def get_data(self, var):
    #return 'ASN1String(*asn_time2UT(NULL,localtime(&(%s)), 0))._get_data()' % var
    return 'ASN1Utime(%s)._get_data()' % var

class BitString(Type):

  classname = 'ASN1BitString'
  typename = 'uint8_t *'
  native = 'BIT_STRING_t'

  def __init__(self):
    Type.__init__(self)
    self.size = (0,0)

  def get_constructor_code(self, name, sep=''):
    r = '%s    m_%s = new %s(pkt->%s, %d);\n' % (sep, name, self.classname, name, self.size[1])
    return r

  def set_size(self, n):
    self.size = n

  def get_getter(self, name, sep=''):
    r = '%s  void get_%s(%s arg) {\n' % (sep, name, self.typename)
    r += '%s    m_%s->get_bits(arg);\n' % (sep, name)
    r += '%s  }\n' % sep
    r += '%s  ASN1BitString & get_%s() {\n' % (sep, name)
    r += '%s    return *m_%s;\n' % (sep, name)
    r += '%s  }\n' % sep
    return r

  def get_setter(self, name, sep=''):
    r = '%s  void set_%s(%s arg) {\n' % (sep, name, self.typename)
    r += '%s    *m_%s = arg;\n' % (sep, name)
    r += '%s  }\n' % sep
    return r

class Integer(BasicType):

  classname = 'long'
  typename = 'long'
  native = 'long'

class Null(BasicType):

  classname = 'NULL_t'
  typename = 'NULL_t'
  native = 'NULL_t'

  def get_header_code(self, sep=''):
    return '%s#include<NULL.h>\n' % sep

class Boolean(BasicType):

  classname = 'BOOLEAN_t'
  typename = 'bool'
  native = 'BOOLEAN_t'

  def get_header_code(self, sep=''):
    return  '%s#include<BOOLEAN.h>\n' % sep

class Oid(Type):

  classname = 'ASN1Oid'
  typename = 'ASN1Oid'
  native = 'OBJECT_IDENTIFIER_t'

  def get_getter(self, name, sep=''):
    r = '%s  %s & get_%s_attr() { return *m_%s;}\n' % (sep, self.typename, name, name)
    r += '%s  string get_%s() { return m_%s->str();}\n' % (sep, name, name)
    return r

  def get_setter(self, name, sep=''):
    #r = Type.get_setter(self, name, sep)
    r = '%s  void set_%s(const string & arg) { *m_%s = arg;}\n' % (sep, name, name)
    return r

class Roid(Oid):

  classname = 'ASN1RelativeOid'
  typename = 'ASN1RelativeOid'

class List(Type):

  basename = 'ASN1Sequence'
  Native = 'A_SET_OF(%s)'

  def __init__(self, innertype):
    Type.__init__(self)
    self.typename = '%s<%s>' % (self.basename, innertype.native)
    self.classname = '%s<%s>' % (self.basename, innertype.native)
    self.native = self.Native % innertype.native
    self.inner = innertype

  def set_module(self, name):
    Type.set_module(self, name)
    if not self.inner.module: self.inner.set_module(name)

  def check_types(self, modules):
    #print 'Lista: check_types', self.inner.__class__, self.inner.name
    if isinstance(self.inner, StubType):
      if not self.inner.module: 
        module = modules[self.module]
      else:
        module = modules[self.inner.module]                
      isLocal = (self.module == module.name)
      t = module.get_member(self.inner.typename, isLocal)
      if t.module != self.module:
        t = modules[t.module].get_member(self.inner.typename)
      #print 'list check_types:', self.inner.name, self.inner.module, self.inner.typename, self.inner.native
      self.inner = t.get_member(self.inner)
      #self.typename = '%s<%s>' % (self.basename, self.inner.typename)
      self.classname = '%s<%s>' % (self.basename, self.inner.native)
      self.native = self.Native % self.inner.native
      self.inner.check_types(modules)
      

  def get_constructor_code(self, name, sep=''):
    r = '%s    m_%s = new %s(&pkt->%s);\n' % (sep, name, self.classname, name)
    return r

  def get_getter(self, name, sep=''):
    #r = Type.get_getter(self, name, sep)
    r = '%s  void get_%s(vector<%s> & v) {\n' % (sep, name, self.inner.typename)
    r += '%s    for (%s::iterator it=m_%s->begin(); it != m_%s->end(); it++) {\n' % (sep, self.classname, name, name)
    r += '%s      v.push_back(%s);\n' % (sep, self.inner.get_instance('*it'))
    r += '%s    }\n' % sep
    r += '%s  }\n' % sep
    return r

  def get_setter(self, name, sep=''):
    #r = Type.get_setter(self, name, sep)
    r = '%s  void set_%s(vector<%s> & v) {\n' % (sep, name, self.inner.typename)
    r += '%s    m_%s->do_empty();\n' % (sep, name)
    r += '%s    for (vector<%s>::iterator it=v.begin(); it != v.end(); it++) m_%s->add(%s);\n' % (sep, self.inner.typename, name, self.inner.get_data('*it'))
    r += '%s  }\n' % sep
    return r

  def dependencies(self):
    r = []
    member = self.inner
    #print self.name, member.typename, member.__class__, isinstance(member, Struct)
    if isinstance(member, Struct):
      r.append(member.typename)
    elif isinstance(member, List):
      r += member.dependencies()
    elif isinstance(member,Composable):
      r += member.dependencies()
    return r

class StubType(Type):

  def __init__(self, typename, module=''):
    Type.__init__(self)
    self.typename = typename
    self.name = typename
    self.native = '%s_t' % typename
    self.module = module # caso seja importado de um modulo

# classe Struct representa um tipo SEQUENCE de um membro de outra SEQUENCE
# Ex: quando um membro eh declarado assim:
#  extra Extra,
# ... sendo Extra um SEQUENCE definido em outra parte da especificacao
class Struct(Type):

  def set_classname(self, name):
    self.typename = 'T%s' % name
    #self.classname = self.typename
    self.classname = name
    self.native = '%s_t' % name

  def get_var_code(self, name, prefix, sep=''):
    r = '%s    %s pld(&%s%s);\n' % (sep, self.typename, prefix, name)
    r += '%s    pld.set_destroy(false);\n' % sep
    return r

  def get_var_decl(self, name, sep=''):
    print ('var_decl:', self.typename)
    r = '%s  %s * m_%s;\n' % (sep, self.typename, name)
    return r

  def get_constructor_code(self, name, sep=''):
    r = '%s    m_%s = new %s(&pkt->%s);\n' % (sep, name, self.typename, name)
    return r

  def get_setvar_code(self, name, prefix, arg, sep=''):
    return ''

  def get_data(self, var=''):
    return '%s->_get_data()' % var

  def get_instance(self, var):
    return '%s(&(%s))' % (self.typename, var)


class Composable(Type):

  Classname = '%s'
  Typename = '%s'
  Generated = []

  def __init__(self, name=''):
    Type.__init__(self)
    self.name = name
    self.container = ''
    self.fields = {}
    self.embed = False
    self.native = '%s_t' % name

  def set_name(self, name):
    self.name = name
    if not self.container: self.classname = self.Classname % self.name
    self.typename = self.Typename % self.name
    for member in self.fields.values():
      if isinstance(member, Composable):
        member.set_container(self.name)
        member.embed = True
    
  def set_container(self, name):
    self.container = name

  def check_types(self, modules):
    d = {}
    ok = False
    for member_name in self.fields:
      member = self.fields[member_name]
      if isinstance(member, StubType):
        if not member.module: 
          module = modules[self.module]
        else:
          module = modules[member.module]                
        isLocal = (self.module == module.name)
        t = module.get_member(member.typename, isLocal)
        if t.module != self.module:
          t = modules[t.module].get_member(member.typename)
        member = t.get_member(member)
        #if isinstance(member, Composable): member.set_container(self.name)
        #print '!!!', member_name, member.typename, member.__class__, 'mod="%s"'%member.module, module.name
        ok = True
      member.check_types(modules)
      d[member_name] = member
      #print '...', member_name, member, 'mod=%s'%member.module
    if ok: self.fields.update(d)

  def set_module(self, name):
    Type.set_module(self, name)
    for member_name in self.fields:
      member = self.fields[member_name]
      #print 'set_module:', self.name, name, 'member=%s'%member_name, 'mod=%s' % member.module
      if not member.module and not isinstance(member, StubType):
        member.set_module(name)

  def set_fields(self, fields):
    self.fields = fields

  def get_member(self, member):
    return member

  def get_header_code(self):
    return '#include<%s.h>\n' % self.name

  def gen_code(self, embed=False, sep=''):
    #print self.name, self.embed, embed
    r = ''
    #print '<< generated:', self.name, self.embed, embed
    if embed != self.embed: raise ValueError('done')
    if self.name in self.Generated: raise ValueError('done')
    self.Generated.append(self.name)
    #if self.name == 'Ativo': return ''
    for member in self.fields.values():
      if isinstance(member, Composable): 
        r += member.gen_code(embed, sep)
    #print '-> generated:', self.name
    return r

  def dependencies(self):
    r = []
    for member in self.fields.values():
      #print self.name, member.typename, member.__class__, isinstance(member, Struct)
      if isinstance(member, Struct):
        r.append(member.typename)
      elif isinstance(member, List):
        r += member.dependencies()
      elif isinstance(member,Composable):
        r += member.dependencies()
    return r

class Enum(Composable):

  def get_member(self, member):
    t = Enumerated(member.typename)
    return t

  def check_types(self, types):
    pass

  def get_header_code(self):
    return '#include<%s.h>\n' % self.name

  def gen_code(self, embed=True, sep=''):
    return ''

class Sequence(Composable):

  Classname = 'ASN1DataType<%s_t>'
  Typename = 'T%s'
  Coders = ['DER', 'XER']

  def __init__(self):
    Composable.__init__(self)

  def __eq__(self, o):
    return self.name == o.name

  def __neq__(self, o):
    return self.name != o.name

  def get_member(self, member):
    t = Struct()
    t.set_classname(member.typename)
    return t

  def get_var_decl(self, name, sep=''):
    #print 'var_decl:', self.typename
    r = '%s  %s * m_%s;\n' % (sep, self.typename, name)
    return r

  def set_name(self, name):
    Composable.set_name(self, name)
    self.native = '%s_t' % self.name

  def set_container0(self, name):
    Composable.set_container(self, name)
    self.native = 'typename %s_t::%s' % (self.container, self.name)
    self.classname = 'ASN1DataType<%s>' % self.native

  def get_encoders_code(self, sep):
    r = ''
    for coder in self.Coders:
      ncoder = coder.capitalize()
      r += '%s  class %sSerializer : public %sSerializer<%s> {\n' % (sep, ncoder, coder, self.native)
      r += '%s  public:\n' % sep
      r += '%s    %sSerializer(ostream & out) : %sSerializer<%s>(&asn_DEF_%s, out) {}\n' % (sep, ncoder, coder, self.native, self.name)
      r += '%s    ~%sSerializer() {}\n' % (sep, ncoder)
      r += '%s    ssize_t serialize(T%s & pkt) {%sSerializer<%s>::serialize(pkt);}\n' % (sep, self.name, coder, self.native)
      r += '%s  };\n' % sep
      r += '%s  class %sDeserializer : public %sDeserializer<%s> {\n' % (sep, ncoder, coder, self.native)
      r += '%s  public:\n' % sep
      r += '%s    %sDeserializer(istream & inp) : %sDeserializer<%s>(&asn_DEF_%s, inp) {}\n' % (sep, ncoder, coder, self.native, self.name)
      r += '%s    ~%sDeserializer() {}\n' % (sep, ncoder)
      r += '%s    T%s * deserialize() {\n' % (sep, self.name)
      r += '%s      ASN1DataType<%s> * p = %sDeserializer<%s>::deserialize();\n' % (sep, self.name, coder, self.native)
      r += '%s      if (not p) return NULL;\n' % sep
      r += '%s      return get_obj(p);\n' % sep
      r += '%s    }\n' % sep
      r += '%s    T%s * scan() {\n' % (sep, self.name)
      r += '%s      ASN1DataType<%s> * p = %sDeserializer<%s>::scan();\n' % (sep, self.name, coder, self.native)
      r += '%s      if (not p) return NULL;\n' % sep
      r += '%s      return get_obj(p);\n' % sep
      r += '%s    }\n' % sep
      r += '%s private:\n' % sep
      r += '%s  T%s * get_obj(ASN1DataType<%s> * p) {\n' % (sep, self.name, self.native)
      r += '%s      T%s * obj = new T%s(p->_get_data());\n' % (sep, self.name, self.name)
      r += '%s      p->set_destroy(false);\n' % sep
      r += '%s      obj->set_destroy(true);\n' % sep
      r += '%s      delete p;\n' % sep
      r += '%s      return obj;\n' % sep
      r += '%s    }\n' % sep
      r += '%s  };\n' % sep
    return r

  def get_header_code(self, sep=''):
    r = '%s#include<%s.h>\n' % (sep, self.name)
    return r

  def get_choices(self):
    return filter(lambda x: isinstance(x, Choice), self.fields.values())

  def __get_methods__(self, sep):
    r = '%s public:\n' % sep
    r += '%s  T%s() : %s(&asn_DEF_%s) {\n' % (sep, self.name, self.classname, self.name)
    #r += '%s    pkt = _get_data();\n' % sep
    r += '%s    init();\n' % sep
    r += '%s  }\n' % sep
    # construtor que recebe uma referencia ao tipo ASN1
    r += '%s  T%s(%s * ptr) : %s(&asn_DEF_%s, ptr) {\n' % (sep, self.name, self.native, self.classname, self.name)
    r += '%s    destroy = false;\n' % sep
    r += '%s    init();\n' % sep
    r += '%s  }\n' % sep
    # construtor de copia
    r += '%s  T%s(const T%s & o) : %s(&asn_DEF_%s, o.pkt) {\n' % (sep, self.name, self.name, self.classname, self.name)
    r += '%s    init();\n' % sep
    r += '%s    destroy = false;\n' % sep
    r += '%s  }\n' % sep
    r += '%s  void init() {\n' % sep
    for name in self.fields:
      member = self.fields[name]
      r += member.get_constructor_code(name, sep)
    r += '%s  }\n' % sep
    r += '%s  virtual ~T%s() {\n' % (sep, self.name)
    for name in self.fields:
      member = self.fields[name]
      r += member.get_destructor_code(name, sep)
    r += '%s  }\n' % sep
    # operador de atribuicao ...
    r += '%s  T%s & operator=(const T%s & o) {\n' % (sep, self.name, self.name)
    r += '%s    if (destroy) delete pkt;\n' % sep
    r += '%s    pkt = o.pkt;\n' % sep
    r += '%s    DESC = o.DESC;\n' % sep
    for name in self.fields:
      member = self.fields[name]
      r += member.get_destructor_code(name, sep)
    r += '%s    init();\n' % sep
    r += '%s    destroy = false;\n' % sep
    r += '%s    return *this;\n' % sep
    r += '%s}\n' % sep
    return r
    
  def gen_code(self, embed=False, sep=''):
    r = ''
    try:    
      r = Composable.gen_code(self, False, sep)
    except:
      return r
    r += '%sclass T%s : public %s {\n' % (sep, self.name, self.classname)
    r += '%s public:\n' % sep
    for member in self.fields.values():
      #print '>>>', member.name, member.__class__, member.typename, member.module
      if isinstance(member, Composable): r += member.gen_code(True, '%s  '%sep)
    r += '%s private:\n' % sep
    #print self.name, self.dependencies()
    for name in self.fields:
      member = self.fields[name]
      #print name, member.typename, member.dependencies()
      r += member.get_var_decl(name, sep)

    r += self.__get_methods__(sep)

    for name in self.fields:
      member = self.fields[name]
      r += self.__get_member__(name, member, sep)
      r += self.__set_member__(name, member, sep)
    r += self.get_encoders_code(sep)
    r += '%s};\n\n' % sep
    return r

  def __get_member__(self, name, member, sep=''):
    return member.get_getter(name, sep)

  def __set_member__(self, name, member, sep=''):
    return member.get_setter(name, sep)

  def __repr__(self):
    return self.name

class Set(Sequence):

  Classname = 'ASN1DataType<%s_t>'
  Typename = 'T%s'
  Coders = ['DER', 'XER']

  def __init__(self):
    Sequence.__init__(self)

  def __get_member__(self, name, member, sep=''):
    r = '%s  %s& get_%s() {\n' % (sep, member.typename, name)
    r += '%s    if (not isPresent(%s_PR_%s)) throw -1;\n' % (sep, self.name, name)
    r += '%s    return get_%s_ok();\n' % (sep, name)
    r += '%s  }\n' % sep
    r += member.get_getter('%s_ok' % name, sep)
    return r

  def __set_member__(self, name, member, sep=''):
    r = '%s  %s& set_%s() {\n' % (sep, member.typename, name)
    r += '%s    make_present(%s_PR_%s);\n' % (sep, self.name, name)
    r += '%s    set_%s_ok();\n' % (sep, name)
    r += '%s  }\n' % sep
    r += member.get_setter('%s_ok' % name, sep)
    return r

  def __get_methods__(self, sep=''):
    r = Sequence.__get_methods__(self, sep)
    r += '%s  void make_present(%s_PR pr) {\n' % (sep, self.name)
    r += '%s    ASN_SET_MKPRESENT(&pkt->_presence_map, pr);\n' % sep
    r += '%s  }\n' % sep 
    r += '%s  bool isPresent(%s_PR pr) {\n' % (sep, self.name)
    r += '%s    return (ASN_SET_ISPRESENT(&pkt, pr) != 0);\n' % sep
    r += '%s  }\n' % sep
    return r

# Transformar choice em uma classe ? melhor para choices aninhados, e
# para a propria estrutura do parser ...
class Choice(Composable):

  Classname = 'Choice_%s'
  Typename = 'Choice_%s'
  #Classname = '%s'
  #Typename = '%s'

  def __init__(self):
    Composable.__init__(self)
    self.embed = True

  def get_check_code(self, sep):
    r = '%s private:\n' % sep
    r += '%s  void check(%s_PR attr) {\n' % (sep, self.name)
    r += '%s    if (pkt->%s.present == %s_PR_NOTHING) pkt->%s.present = attr;\n' % (sep, self.name, self.name, self.name)
    r += '%s    else if (pkt->%s.present != attr) throw -1;\n' % (sep, self.name)
    r += '%s  }\n' % sep
    r += '%s public:\n' % sep
    return r

  def get_member(self, member):
    t = Choice()
    t.set_name(member.name)
    return t

  def gen_code(self, embed=True, sep=''):
    r = ''
    try:    
      r = Composable.gen_code(self, embed, sep)
    except Exception as e:
      #print '...', e
      #traceback.print_exc()
      return r
    if self.container:
      typename = 'typename %s_t::%s' % (self.container, self.name)
    else:
      typename = '%s_t' % self.name
    r = '%sclass %s {\n' % (sep, self.typename)
    r += '%s private:\n' % sep
    r += '%s  %s * ptr;\n' % (sep, typename)
    r += '%s  void check(%s_PR attr) {\n' % (sep, self.name)
    r += '%s    if (ptr->present == %s_PR_NOTHING) ptr->present = attr;\n' % (sep, self.name)
    r += '%s    if (ptr->present != attr) throw -1;\n' % sep
    r += '%s  }\n' % sep
    r += '%s public:\n' % sep
    r += '%s  %s(%s & rec) : ptr(&rec) {\n' % (sep, self.typename, typename)
    r += '%s  }\n' % sep
    r += '%s  %s(%s & rec, bool reset) : ptr(&rec) {\n' % (sep, self.typename, typename)
    r += '%s    if (reset) ptr->present = %s_PR_NOTHING;\n' % (sep, self.name)
    r += '%s  }\n' % sep
    r += '%s  ~%s() {}\n' % (sep, self.typename)
    r += '%s  %s_PR get_choice() { return ptr->present;}\n' % (sep, self.name)
    for name in self.fields:
      item = self.fields[name]
      #print item, item.__class__
      r += '%s  void set_%s() { ptr->present = %s_PR_%s; }\n' % (sep, name, self.name, name)
      r += '%s  void set_%s(const %s & arg) {\n' % (sep, name, item.typename)
      r += '%s    ptr->present = %s_PR_%s;\n' % (sep, self.name, name)
      r += item.get_setvar_code(name, 'ptr->choice.', 'arg', '%s    ' % sep)
      r += '%s  }\n' % sep
      r += '%s  %s get_%s() {\n' % (sep, item.typename, name)
      r += '%s    check(%s_PR_%s);\n' % (sep, self.name, name)
      r += item.get_var_code(name, 'ptr->choice.', sep)
      r += '%s    return pld;\n' % sep
      r += '%s  }\n' % sep
    r += '%s};\n\n' % sep
    return r

  def get_getter(self, name, sep=''):
    r = '%s  %s & get_%s() { return *m_%s;}\n' % (sep, self.typename, name, name)
    return r

  def get_setter(self, name, sep=''):
    return ''

  def get_constructor_code(self, name, sep=''):
    r = '%s    m_%s = new %s(pkt->%s, destroy);\n' % (sep, name, self.typename, name)
    return r

  def get_destructor_code(self, name, sep=''):
    return '%s    delete m_%s;\n' % (sep, name)

class Module:

  def __init__(self, name):
    self.name = name
    self.members = {}
    self.external = []

  def add_members(self, members):
    #print 'add_members:', self.name, 'members=%s'%members
    for member in members:
      if not member.module:
        if not isinstance(member, StubType): member.set_module(self.name)
      else:
        if not member.module in self.external: self.external.append(member.module)
      #print '%s: %s/%s/%s/%s' % (self.name, member.name, member.__class__,member.typename, member.module)
      self.members[member.name] = member

  def set_exportable(self, exports=[]):
    for name in exports:
      try:
        self.members[name].set_exportable()
      except KeyError:
        raise ValueError('tipo "%s" nao pode ser exportado no modulo "%s"' % (name, self.name))

  def get_member(self, name, isLocal=False):
    #print '---', self.name, name, isLocal, self.members.keys()
    member = self.members[name]
    if not isLocal:
      if not member.exportable: raise ValueError('tipo "%s" nao exportavel no modulo "%s"' % (name,self.name))
    return member

  def add_external(self, name):
    self.external.append(name)

  def get_members(self):
    # reordena os tipos de acordo com suas dependencias ...
    orig = list(self.members.values())
    tipos = []
    members = []
    while orig:
      for field in orig:
        ok = True
        print ('>>', field)
        for m in field.dependencies():
          print ('--', field.name, m)
          if not m in tipos:
            ok = False
            break
        if ok:
          members.append(field)
          tipos.append(field.typename)
          orig.remove(field)
          break
          
    return members

  def gen_header(self, modules):
    r = '#ifndef ASN1_PARSER_%s_H\n' % self.name.upper()
    r += '#define ASN1_PARSER_%s_H\n\n' % self.name.upper()
    r += '#include <asn1++/asn1++.h>\n\n'
    for arq in self.external:
      r += '#include <parser_%s.h>\n' % arq

    for member in self.members.values():
      #if isinstance(member, Composable):
      #print self.name, member, 'module=%s' % member.module
      member.check_types(modules)
    # OBS: aqui reordenar os tipos de acordo com suas dependencias ...
    members = self.get_members()    
    for member in members:
      r += member.get_header_code()
    r += '\n'
    for member in members:
      if isinstance(member, Composable):
        #print member.name, member.Generated
        r += member.gen_code(False, '')
    r += '#endif\n'
    return r
