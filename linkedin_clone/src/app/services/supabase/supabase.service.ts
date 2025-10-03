import { Injectable } from '@angular/core';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { SupabaseConstants } from '../../constants/supabase.constants';

@Injectable({
  providedIn: 'root'
})
export class SupabaseService {
  private supabase: SupabaseClient;

  constructor() {
    this.supabase = createClient(
      SupabaseConstants.supabaseUrl,
      SupabaseConstants.supabaseKey
    );
  }

  get client(): SupabaseClient {
    return this.supabase;
  }

  getPublicUrl(bucket: string, path: string): string{
    return this.client.storage.from(bucket).getPublicUrl(path).data.publicUrl;
  }
}
