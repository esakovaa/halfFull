import { scryptSync, timingSafeEqual } from 'node:crypto';
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

function getSupabaseAdmin() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { persistSession: false } });
}

function verifyPassword(password: string, stored: string): boolean {
  try {
    const [salt, hash] = stored.split(':');
    const candidate = scryptSync(password, salt, 64).toString('hex');
    return timingSafeEqual(Buffer.from(hash, 'hex'), Buffer.from(candidate, 'hex'));
  } catch {
    return false;
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json() as { login?: unknown; password?: unknown };
    const login = typeof body.login === 'string' ? body.login.trim() : '';
    const password = typeof body.password === 'string' ? body.password : '';

    if (!login || !password) {
      return NextResponse.json({ error: 'Login and password are required.' }, { status: 400 });
    }

    const supabase = getSupabaseAdmin();
    if (!supabase) {
      return NextResponse.json({ error: 'Supabase is not configured.' }, { status: 500 });
    }

    const { data, error } = await supabase
      .from('app_accounts')
      .select('login, password_hash, anonymous_id')
      .eq('login', login)
      .single();

    if (error || !data) {
      return NextResponse.json({ error: 'Invalid login or password.' }, { status: 401 });
    }

    if (!verifyPassword(password, data.password_hash as string)) {
      return NextResponse.json({ error: 'Invalid login or password.' }, { status: 401 });
    }

    return NextResponse.json({ ok: true, login: data.login, anonymousId: data.anonymous_id });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Could not log in.' },
      { status: 400 }
    );
  }
}
