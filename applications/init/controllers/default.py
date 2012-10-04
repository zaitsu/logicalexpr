# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

def echo():
    import random
    expr = ['toBe & ~toBe',
            '(p & q) | (~p & ~q)',
            '(p & ~q) & ~p | q',
            '(~r | t | ~s) & (r -> s) & ~(r -> t)',
            '(~q & (~(h -> q) | (~q & h))) | (~h & ~q) | ~(~q & ~h)']
    example = expr[random.randint(0,4)]
    return "$('#in').val(%s);" % repr(example)

def table(expr):
    from tokenize import generate_tokens
    from StringIO import StringIO

    def generate(expr):
        readline = StringIO(expr).readline
        tokens = [t[1] for t in generate_tokens(readline)][:-1]
        return eqv_expr(tokens)

    def eqv_expr(tokens):
        value = imp_expr(tokens)
        while tokens and \
                ((tokens[0] == '<=' and tokens[1] == '>') or
                 (tokens[0] == '<' and tokens[1] =='-' and tokens[2] == '>')):
            _ = tokens.pop(0)
            _ = tokens.pop(0)
            if tokens[0] == '>': _ = tokens.pop(0)
            right = imp_expr(tokens)
            value = (value == right)
        return value

    def imp_expr(tokens):
        value = rimp_expr(tokens)
        while tokens and tokens[0] in ('=','-') and tokens[1] == '>':
            _ = tokens.pop(0)
            _ = tokens.pop(0)
            right = rimp_expr(tokens)
            value = not value or right
        return value

    def rimp_expr(tokens):
        value = or_expr(tokens)
        while tokens and \
                ((tokens[0] == '<=' and tokens[1] != '>') or
                 (tokens[0] == '<' and tokens[1] == '-' and tokens[2] != '>')):
            _ = tokens.pop(0)
            if tokens[0] == '-': _ = tokens.pop(0)
            right = or_expr(tokens)
            value = value or not right
        return value

    def or_expr(tokens):
        value = and_expr(tokens)
        while tokens and tokens[0] in ('|'):
            _ = tokens.pop(0)
            right = and_expr(tokens)
            value = value or right
        return value

    def and_expr(tokens):
        value = not_expr(tokens)
        while tokens and tokens[0] in ('&'):
            _ = tokens.pop(0)
            right = not_expr(tokens)
            value = value and right
        return value

    def not_expr(tokens):
        invert = False
        while tokens and tokens[0] == '~':
            _ = tokens.pop(0)
            invert = not invert
        value = atom(tokens)
        if invert:
            value = not value
        return value

    def atom(tokens):
        if tokens and tokens[0] == '(':
            _ = tokens.pop(0)
            value = eqv_expr(tokens)
            _ = tokens.pop(0)
        else:
            ident = tokens.pop(0)
            value = variable[ident]
        return value

    def combos(variable,varlist):
        if varlist == []:
            yield []
        else:
            for variable[varlist[0]] in (True, False):
                for rest in combos(variable,varlist[1:]):
                    yield [variable[varlist[0]]] + rest

    keywords = ['&','|','=','-','~','=','>','<=','<','(',')']
    readline = StringIO(expr).readline
    variable = {}
    htmlstct = []
    for token in generate_tokens(readline):
        text = token[1]
        if text != '' and text not in keywords:
            variable[text] = text
    varlist = sorted(variable.keys())
    variable['result'] = expr
    for _ in combos(variable, varlist):
        variable['result'] = generate(expr)
        htmlstct.append(variable.copy())
    return (varlist, htmlstct)

def errormsg(msg):
    return '<div class="alert alert-error"><a class="close" data-dismiss="alert">x</a><strong>Error!</strong> %s</div>' % msg

def createtable():
    results = []
    if not request.vars.e:
        return "$('#target').html(%s);$('.alert').alert();" % repr(errormsg('Invalid'))
    else:
        chkexpr = request.vars.e.replace('#','!')
        invalid = ['--','==','=-','-=','&&','||','>>','<<','~-','~=','~&','~|','|&','&|']
        keyword = ['<->','<=>','<=','<-','=>','->','|','&','~',' ','(',')']
        for i in invalid:
            if chkexpr.find(i) >= 0: 
                return "$('#target').html(%s);$('.alert').alert();" % repr(errormsg('Invalid Expression.'))
        for k in keyword: chkexpr = chkexpr.replace(k,'#'*len(k))
        chkexpr = ''.join(map((lambda c: '#' if str.isalpha(c) else c), list(chkexpr)))
        #return '<p>%s:%s invalid expression!</p>' % (request.vars.e,chkexpr)
        if chkexpr.count('#') == len(chkexpr) and \
                request.vars.e.count('(') == request.vars.e.count(')'):
            (header, results) = table(request.vars.e.strip())
        else:
            return "$('#target').html(%s);$('.alert').alert();" % repr(errormsg('Invalid Expression.'))
    if results:
        trows = []
        thead = [TH(v) for v in header] + [TH(request.vars.e)]
        for r in results:
            temp = []
            for k in header: temp += TR(r.get(k))
            temp += TR(r.get('result'))
            trows.append(temp)
        retval = TABLE(THEAD(TR(*thead)),TBODY(*trows), _class="table table-striped table-bordered").xml()
        return "$('#target').html(%s);" % repr(retval)
    else:
        return "$('#target').html(%s);$('.alert').alert();" % repr(errormsg('Unknown Error!'))

def index():
    return locals()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
