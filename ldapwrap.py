import ldap

def connect(host):
    try:
        l = ldap.open(host)
        l.protocol_version = ldap.VERSION3
        return l
    except ldap.LDAPError, e:
        print 'Connection fail: '+host
        print e


def bind(conn, username, password):
    try:
        conn.simple_bind_s(username, password)
        return 1
    except ldap.LDAPError, e:
        print 'ldap bind fail '+username
        return 0


def getUser(conn, baseDN, searchFilter, user):
    searchScope = ldap.SCOPE_SUBTREE
    retrieveAttributes = ['uid', 'cn']
    searchFilter += "(uid="+user+"))"

    try:
        result_set = conn.search_s(baseDN, searchScope, searchFilter, retrieveAttributes)
        if len(result_set) == 1:
            #return attribs
            result = result_set[0][1]
            result['dn'] = result_set[0][0]
            return result
        else:
            #user doesnt exist
            return None
    except ldap.LDAPError, e:
        print 'ERROR:'
        print e
