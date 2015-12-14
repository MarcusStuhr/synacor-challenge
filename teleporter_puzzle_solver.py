#see notes.txt for explanation behind this solver

MOD = 2**15

for c in xrange(1,MOD+1):
    denom = c
    mod = denom*MOD
    exponent = ((c - 1 + (1 + c)**(3 + c))/c)
    ans = (((pow(1 + c, exponent, mod)- 1)% mod)/c % mod - 2) % MOD
    
    if ans==6:
        print "A(4,1,%s) mod %s = 6" % (c,MOD)
        break