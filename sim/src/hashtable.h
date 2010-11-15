// Copyright 2005-2006 Nanorex, Inc.  See LICENSE file for details. 
#ifndef HASHTABLE_H_INCLUDED
#define HASHTABLE_H_INCLUDED

#define RCSID_HASHTABLE_H  "$Id: hashtable.h 9214 2007-05-11 04:41:33Z emessick $"

struct hashtable_bucket
{
  int hash;
  char *key;
  void *value;
};


struct hashtable 
{
  int size; /* length of buckets array */
  int count; /* number of items (full buckets) in the hashtable */
  struct hashtable_bucket *buckets;
};

extern struct hashtable *hashtable_new(int initial_size);

extern void *hashtable_put(struct hashtable *table, char *key, void *value);

extern void *hashtable_get(struct hashtable *table, char *key);

extern void hashtable_print(FILE *f, struct hashtable *table);

extern void hashtable_iterate(struct hashtable *table, void func(char *key, void *value));

extern void hashtable_destroy(struct hashtable *table, void func(void *value));

#endif
