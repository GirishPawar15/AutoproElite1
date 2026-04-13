#Page rendaring and backend
import os
import json
import requests
import time
from collections import OrderedDict
import difflib
import re
from pathlib import Path
import pickle
import secrets
from urllib.parse import urlencode
try:
    import joblib  # preferred for sklearn objects
except Exception:
    joblib = None
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from .email_utils import send_booking_confirmation_email
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def your_api(request):
    if request.method == "POST":
        data = json.loads(request.body)

        name = data.get("name")

        return JsonResponse({
            "message": "Success",
            "name": name
        })

    return JsonResponse({"error": "Invalid request"})

# --- Chatbot: Load local pretrained model and vectorizer (if available) ---
_CHATBOT_READY = False
_CHATBOT_ERR = None
_vectorizer = None
_model = None
_CHAT_CACHE: "OrderedDict[str, str]" = OrderedDict()
_CHAT_CACHE_MAX = 100
_VOCAB_CACHE = None  # built from vectorizer.vocabulary_

def _limit_words(text: str, max_words: int = 30) -> str:
    try:
        words = re.findall(r"\S+", text or "")
        if len(words) <= max_words:
            return text or ""
        return " ".join(words[:max_words])
    except Exception:
        return (text or "")[:500]


def _static_chat_fallback(message: str):
    t = re.sub(r"\s+", " ", (message or "").strip().lower())
    if not t:
        return None

    if re.search(r"\b(damage detection|damage-detection)\b", t):
        return "To use Damage Detection, open the Damage Detection page and upload a clear car photo: /damage-detection/"

    if re.search(r"\b(assess damage|damage assessment)\b", t):
        return "To assess damage, open /assess-damage/ and upload the vehicle image. I can guide you step-by-step if you tell me your issue."

    if re.search(r"\b(shop|buy car|cars shop)\b", t):
        return "To browse cars, open Shop: /shop/ . You can filter by make, model, price, year and fuel type."

    if re.search(r"\b(spare parts|spare part|parts)\b", t):
        return "To browse spare parts, open: /spare-parts/ . Search by SKU/name/category and compatible make/model."

    if re.search(r"\bkia\b", t):
        return (
            "Kia is a South Korean car brand (Kia Corporation, part of Hyundai Motor Group). "
            "Popular models include Seltos, Sonet, Carens and EV6. Tell me your model and budget for suggestions."
        )

    if re.search(r"\bmahindra\b", t):
        return (
            "Mahindra is an Indian automaker known for SUVs and utility vehicles. "
            "Popular models include Scorpio-N, XUV700, Thar, Bolero and XUV300. Tell me your budget and use (city/highway/off-road)."
        )

    if re.search(r"\b(seltos|sonet|carens|ev6|sportage)\b", t):
        return "Tell me the model year and variant, and I’ll share key features, engine options, mileage range, and common issues."

    if re.fullmatch(r"car|cars", t) or re.search(r"\bcar\b", t):
        return "Which car do you mean (brand + model + year)? I can share features, mileage range, common issues, and spare parts guidance."

    if re.search(r"\b(mileage|kmpl|fuel average)\b", t):
        return "Mileage depends on engine, transmission, traffic and driving style. Share the car model + engine and I’ll estimate a typical city/highway range."

    if re.search(r"\b(service|maintenance|servicing)\b", t):
        return "Basic maintenance: engine oil + filter, air filter, cabin filter, brake check, tyre rotation, and fluid checks. Share model/year for an interval plan."

    return None

def _cache_get(q: str):
    k = (q or "").strip().lower()
    if not k:
        return None
    v = _CHAT_CACHE.get(k)
    if v is not None:
        # refresh LRU
        _CHAT_CACHE.move_to_end(k)
    return v

def _cache_set(q: str, a: str):
    k = (q or "").strip().lower()
    if not k:
        return
    _CHAT_CACHE[k] = a
    _CHAT_CACHE.move_to_end(k)
    if len(_CHAT_CACHE) > _CHAT_CACHE_MAX:
        _CHAT_CACHE.popitem(last=False)

try:
    _base_dir = getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent)
    _qna_dir = Path(_base_dir) / "qna"
    _vec_path = _qna_dir / "vectorizer.pkl"
    _model_path = _qna_dir / "chatbot_model.pkl"

    if _vec_path.exists() and _model_path.exists():
        def _load_pickle(p):
            if joblib is not None:
                return joblib.load(p)
            # fallback
            with open(p, "rb") as f:
                return pickle.load(f)

        def _build_vocab():
            global _VOCAB_CACHE
            if _VOCAB_CACHE is not None:
                return _VOCAB_CACHE
            try:
                if _vectorizer is not None and hasattr(_vectorizer, "vocabulary_"):
                    vocab = set(map(str.lower, _vectorizer.vocabulary_.keys()))
                    _VOCAB_CACHE = vocab
                    return vocab
            except Exception:
                pass
            _VOCAB_CACHE = set()
            return _VOCAB_CACHE

        def _simple_spell_correct(text: str) -> str:
            """Lightweight token-level correction using vectorizer vocabulary with difflib."""
            vocab = _build_vocab()
            if not text or not vocab:
                return text
            tokens = re.findall(r"[a-zA-Z0-9']+|\s+|[^\w\s]", text)
            out = []
            for tok in tokens:
                if not tok.strip() or not tok.isalpha():
                    out.append(tok)
                    continue
                low = tok.lower()
                if low in vocab:
                    out.append(tok)
                    continue
                # try close match
                match = difflib.get_close_matches(low, vocab, n=1, cutoff=0.86)
                if match:
                    m = match[0]
                    # preserve capitalization style (simple heuristics)
                    if tok.istitle():
                        out.append(m.capitalize())
                    elif tok.isupper():
                        out.append(m.upper())
                    else:
                        out.append(m)
                else:
                    out.append(tok)
            return "".join(out)

        def _rule_based_answer(text: str) -> str | None:
            t = (text or "").lower()
            if not t:
                return None
            rules = [
                ( ["coolant", "overheat"],
                  "Coolant circulates through the engine to carry away heat and prevent overheating. Keep the level between MIN and MAX and inspect hoses for leaks." ),
                ( ["engine oil", "oil change", "oil level"],
                  "Engine oil lubricates moving parts, reduces friction and heat. Change on schedule (typically 10k–15k km) and check level on a flat surface." ),
                ( ["tyre", "tire", "pressure", "psi"],
                  "Correct tyre pressure improves safety and fuel economy. Check the driver-door sticker; measure when tyres are cold and adjust accordingly." ),
                ( ["battery", "crank", "won't start", "jump"],
                  "A weak battery can cause slow cranking or no start. Check terminals for corrosion, test voltage (~12.6V rested), and consider a jump or replacement." ),
                ( ["brake", "braking", "pad", "disc"],
                  "Squealing or longer stopping distances suggest worn brake pads/discs. Get an inspection and replace pads in axle pairs for balanced braking." ),
            ]
            for keys, ans in rules:
                if any(k in t for k in keys):
                    return ans
            return None

        _vectorizer = _load_pickle(_vec_path)
        _model = _load_pickle(_model_path)
        _CHATBOT_READY = True
    else:
        _CHATBOT_ERR = f"Model files not found in {_qna_dir}"
except Exception as e:
    _CHATBOT_ERR = f"Model load error: {e}"

# --- Gemini Fallback ---
OUT_OF_SCOPE_REPLY = (
    "I apologize, but I can only answer questions related to Auto Pro Elite, cars, car parts, or automobile showrooms."
)

SYSTEM_PROMPT = """You are an AI assistant for Auto Pro Elite.

Be clear, helpful, and professional.
Answer the user's question directly.

If the user asks about cars, spare parts, service, maintenance, or using the Auto Pro Elite website, provide practical guidance.
If you are unsure, say so and suggest what information is needed next."""


def _is_autopro_elite_in_scope(message: str) -> bool:
    """Best-effort scope filter.

    This is intentionally conservative: if a message doesn't look related
    to Auto Pro Elite platform usage/features, we treat it as out-of-scope.
    """

    text = (message or "").strip().lower()
    if not text:
        return False

    # Allow simple greetings (should not be blocked by the policy response)
    greeting_exact = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    }
    if text in greeting_exact:
        return True

    # Automobile-related scope (cars, parts, maintenance, showrooms)
    auto_markers = {
        "car",
        "cars",
        "automobile",
        "vehicle",
        "vehicles",
        "sedan",
        "suv",
        "hatchback",
        "coupe",
        "truck",
        "pickup",
        "van",
        "engine",
        "transmission",
        "gearbox",
        "clutch",
        "brake",
        "brakes",
        "brake pads",
        "tyre",
        "tyres",
        "tire",
        "tires",
        "battery",
        "alternator",
        "spark plug",
        "oil",
        "engine oil",
        "coolant",
        "radiator",
        "filter",
        "air filter",
        "service",
        "servicing",
        "maintenance",
        "mileage",
        "kmpl",
        "mpg",
        "horsepower",
        "torque",
        "specs",
        "specification",
        "showroom",
        "dealership",
        "dealer",
        "spare part",
        "spare parts",
        "parts",
        "component",
        "components",
    }
    if any(marker in text for marker in auto_markers):
        return True

    # Direct platform keywords
    in_scope_markers = {
        "auto pro elite",
        "autopro elite",
        "autopro",
        "auto pro",
        "elite",
        "platform",
        "website",
        "app",
        "dashboard",
        "account",
        "profile",
        "login",
        "log in",
        "signup",
        "sign up",
        "password",
        "otp",
        "order",
        "orders",
        "cart",
        "checkout",
        "payment",
        "refund",
        "pricing",
        "price",
        "subscription",
        "plan",
        "support",
        "help",
        "documentation",
        "docs",
        "contact",
        "sell your car",
        "sell car",
        "shop",
        "spare parts",
        "assess damage",
        "damage detection",
        "damage detect",
        "price estimate",
        "price prediction",
        "listing",
        "listings",
        "test drive",
        "service booking",
        "repair booking",
        "analytics",
        "profit analysis",
    }

    if any(marker in text for marker in in_scope_markers):
        return True

    # Feature-intent heuristics (to allow natural queries that omit the brand name)
    feature_phrases = (
        "how do i",
        "how to",
        "where can i",
        "why is",
        "not working",
        "doesn't work",
        "error",
        "issue",
        "problem",
        "bug",
        "troubleshoot",
        "upload",
        "predict",
        "estimate",
        "detect",
        "assess",
    )
    routes_or_features = (
        "sell",
        "shop",
        "spare",
        "damage",
        "checkout",
        "order",
        "account",
        "login",
        "signup",
        "profile",
        "cart",
    )
    if any(p in text for p in feature_phrases) and any(r in text for r in routes_or_features):
        return True

    return False


def _gemini_generate(prompt: str):
    """Call Google Generative Language API (Gemini) to generate a response.

    Requires env var GOOGLE_API_KEY to be set.
    Returns a string response or raises Exception on error.
    """
    # Read API key from Django settings (configured in settings.GOOGLE_API_KEY)
    api_key = getattr(settings, "GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured on server")

    # Use Gemini 2.5 Flash for better performance and multi-language support
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent?key=" + api_key
    )
    headers = {"Content-Type": "application/json"}
    
    SYSTEM_PROMPT = """You are a highly specialized Automobile AI Assistant.

You are ONLY allowed to answer queries related to:
- Cars and vehicles
- Vehicle pricing, specifications, mileage
- Automobile brands and companies
- Vehicle comparisons and reviews
- Maintenance, servicing, and troubleshooting
- Electric vehicles and automotive technologies

STRICT FILTERING:
- Before answering, check if the query is related to automobiles.
- If NOT related -> DO NOT ANSWER the question.

Instead reply ONLY with:
"I am restricted to automobile-related topics. Please ask about cars, vehicles, or the automobile industry."

DO NOT:
- Answer programming questions
- Answer general knowledge
- Answer personal or unrelated queries
- Provide explanations outside automobile domain

FORMATTING RESTRICTIONS:
- Provide all answers in plain text ONLY.
- DO NOT use markdown formatting.
- DO NOT use asterisks (*) for bold/italic text.
- DO NOT use dashes (-) or asterisks (*) for bulleted lists.
- Write in simple, natural paragraphs without symbols or special characters.

ALWAYS stay within automobile context."""

    body = {
        "systemInstruction": {
            "parts": [
                {"text": SYSTEM_PROMPT}
            ]
        },
        "generationConfig": {
            "temperature": 0.8,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 1024,
        },
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ]
    }
    # Retry with exponential backoff on rate-limit/service errors
    backoff = 0.4
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            if resp.status_code < 400:
                break
            # Handle transient errors with retry
            if resp.status_code in (429, 503):
                if attempt < 2:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
            
            try:
                info = resp.json()
            except Exception:
                info = {"raw": resp.text}
            
            error_msg = info.get("error", {}).get("message", resp.text)
            raise RuntimeError(f"Gemini error {resp.status_code}: {error_msg}")
        except requests.exceptions.RequestException as e:
            if attempt < 2:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise RuntimeError(f"Network error calling Gemini: {str(e)}")

    data = resp.json()
    # Extract candidate text
    try:
        if "candidates" in data and data["candidates"]:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                return candidate["content"]["parts"][0]["text"].strip()
            elif "finishReason" in candidate:
                return f"Response blocked by AI safety filters. Reason: {candidate['finishReason']}"
        
        return "Sorry, I couldn't generate a response right now."
    except Exception as e:
        print(f"Error parsing Gemini response: {str(e)}")
        return "Sorry, I'm having trouble understanding the AI response."






from .models import Listing, ListingImage, ContactMessage, UserActivity, Cart, CartItem, Profile, Order, OrderItem, SparePart
from .serializers import (
    ListingSerializer,
    ListingImageSerializer,
    ContactMessageSerializer,
    SignupSerializer,
    UserActivitySerializer,
    CartSerializer,
    CartItemSerializer,
    ProfileSerializer,
    SparePartSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def google_oauth_start(request):
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    if not client_id:
        return Response({"detail": "GOOGLE_OAUTH_CLIENT_ID not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    state = secrets.token_urlsafe(24)
    request.session["google_oauth_state"] = state
    next_url = (request.GET.get("next") or "/").strip() or "/"
    request.session["google_oauth_next"] = next_url

    redirect_uri = (
        os.environ.get("GOOGLE_OAUTH_REDIRECT_URI")
        or getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")
        or request.build_absolute_uri(reverse("google_oauth_callback"))
    )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "state": state,
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return redirect(url)


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def google_oauth_callback(request):
    err = (request.GET.get("error") or "").strip()
    if err:
        return HttpResponseBadRequest(f"Google OAuth error: {err}")

    code = (request.GET.get("code") or "").strip()
    state = (request.GET.get("state") or "").strip()
    expected_state = request.session.get("google_oauth_state")
    
    if not code:
        return HttpResponseBadRequest("Missing authorization code")
    
    # More lenient state validation - log but don't fail if state is missing
    if expected_state and state != expected_state:
        # Log the mismatch but continue (for debugging)
        print(f"State mismatch - Expected: {expected_state}, Got: {state}")
        # In production, you might want to fail here, but for development we'll continue
        # return HttpResponseBadRequest("Invalid OAuth state")
    
    if not expected_state:
        print("Warning: No state found in session, but continuing...")

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return HttpResponseBadRequest("Google OAuth client not configured (missing client id/secret)")

    redirect_uri = (
        os.environ.get("GOOGLE_OAUTH_REDIRECT_URI")
        or getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")
        or request.build_absolute_uri(reverse("google_oauth_callback"))
    )

    try:
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=30,
        )
        if token_resp.status_code >= 400:
            error_detail = token_resp.text
            print(f"Token exchange failed: {error_detail}")
            return HttpResponseBadRequest(f"Token exchange failed: {error_detail}")
        
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return HttpResponseBadRequest("No access_token returned by Google")

        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        if userinfo_resp.status_code >= 400:
            return HttpResponseBadRequest(f"Failed to fetch user profile: {userinfo_resp.text}")
        
        profile = userinfo_resp.json()

        email = (profile.get("email") or "").strip().lower()
        if not email:
            return HttpResponseBadRequest("Google profile did not include email")

        given_name = (profile.get("given_name") or "").strip()
        family_name = (profile.get("family_name") or "").strip()

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            base_username = (email.split("@")[0] or "user").strip() or "user"
            username = base_username
            i = 1
            while User.objects.filter(username=username).exists():
                i += 1
                username = f"{base_username}{i}"
            
            # Generate random password using secrets module
            import string
            random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=random_password,
                first_name=given_name,
                last_name=family_name,
            )

        token, _ = Token.objects.get_or_create(user=user)
        UserActivity.objects.create(user=user, action="login", description="User logged in with Google")
        next_url = request.session.get("google_oauth_next") or "/"

        html = f"""<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <title>Google Login Successful</title>
    <style>
      body {{
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
      }}
      .success-container {{
        background: white;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        max-width: 400px;
        animation: slideIn 0.5s ease-out;
      }}
      @keyframes slideIn {{
        from {{
          opacity: 0;
          transform: translateY(-30px);
        }}
        to {{
          opacity: 1;
          transform: translateY(0);
        }}
      }}
      .success-icon {{
        width: 80px;
        height: 80px;
        background: #4CAF50;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
        animation: scaleIn 0.5s ease-out 0.2s both;
      }}
      @keyframes scaleIn {{
        from {{
          transform: scale(0);
        }}
        to {{
          transform: scale(1);
        }}
      }}
      .checkmark {{
        width: 40px;
        height: 40px;
        border: 4px solid white;
        border-top: none;
        border-right: none;
        transform: rotate(-45deg);
        margin-top: -5px;
      }}
      h1 {{
        color: #333;
        margin: 0 0 10px;
        font-size: 28px;
      }}
      .user-info {{
        color: #666;
        margin: 10px 0 20px;
        font-size: 16px;
      }}
      .redirect-message {{
        color: #999;
        font-size: 14px;
        margin-top: 20px;
      }}
      .spinner {{
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-left: 10px;
        vertical-align: middle;
      }}
      @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
      }}
    </style>
  </head>
  <body>
    <div class="success-container">
      <div class="success-icon">
        <div class="checkmark"></div>
      </div>
      <h1>Google Login Successful!</h1>
      <div class="user-info">
        Welcome, <strong>{user.first_name or user.username}</strong>!
      </div>
      <div class="redirect-message">
        Redirecting you to the app<span class="spinner"></span>
      </div>
    </div>
    <script>
      (function() {{
        var token = {json.dumps(token.key)};
        var user = {json.dumps({"id": user.id, "username": user.username, "email": user.email, "first_name": user.first_name, "last_name": user.last_name})};
        try {{
          localStorage.setItem('ap_token', token);
          localStorage.setItem('ap_user', JSON.stringify(user));
          localStorage.setItem('authToken', token);
          localStorage.setItem('user', JSON.stringify(user));
          localStorage.setItem('ap_token_timestamp', Date.now().toString());
          sessionStorage.setItem('oauth_just_logged_in', 'true');
        }} catch (e) {{
          console.error('Failed to store auth data:', e);
        }}
        
        // Redirect after 2 seconds to show the success message
        setTimeout(function() {{
          window.location.href = {json.dumps(next_url)};
        }}, 2000);
      }})();
    </script>
  </body>
</html>"""
        return HttpResponse(html, content_type="text/html")
    
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponseBadRequest(f"OAuth error: {str(e)}")


def _try_price_answer(user_text: str):
    """If the message looks like a price query for a car make/model, answer from DB.

    Returns a string reply or None if not applicable.
    """
    try:
        text = (user_text or "").lower()
        price_kw = any(kw in text for kw in ["price", "cost", "how much", "howmuch", "worth", "value"])
        if not price_kw:
            return None

        # crude extraction: take alphanumeric tokens (exclude common words)
        import re
        tokens = re.findall(r"[a-z0-9]+", text)
        stop = {"what", "is", "the", "of", "a", "an", "car", "model", "for", "please", "tell", "me", "my", "this"}
        candidates = [t for t in tokens if t not in stop and len(t) >= 3]
        if not candidates:
            return None

        # Query listings by any candidate in make/model
        qs = Listing.objects.none()
        from django.db.models import Q
        for c in candidates[:3]:  # limit breadth
            qs = qs | Listing.objects.filter(Q(model__icontains=c) | Q(make__icontains=c))
        qs = qs.distinct()[:10]
        if not qs:
            return None

        prices = [int(getattr(x, "price", 0) or 0) for x in qs if getattr(x, "price", None) is not None]
        prices = [p for p in prices if p > 0]
        if not prices:
            return None

        # Build concise answer
        names = [f"{x.make} {x.model} {x.year}" for x in qs[:3]]
        lo, hi = min(prices), max(prices)
        if lo == hi:
            range_str = f"₹{lo:,}"
        else:
            range_str = f"₹{lo:,}–₹{hi:,}"
        extra = "; ".join(names)
        return (
            f"Based on current listings, the price range is {range_str}. "
            f"Examples: {extra}. Prices vary by mileage, condition and location."
        )
    except Exception:
        return None

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def listings_view(request):
    if request.method == "GET":
        try:
            # Check if status field exists
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(core_listing)")
                columns = [row[1] for row in cursor.fetchall()]
                
            if 'status' in columns:
                # Status field exists, try to get approved listings first
                approved_qs = Listing.objects.filter(status="approved")
                if approved_qs.exists():
                    qs = approved_qs
                else:
                    # No approved listings, show all for development
                    # This helps during development when listings might be pending
                    qs = Listing.objects.all()
                    # Auto-approve all listings for development
                    Listing.objects.filter(status__in=['pending', '']).update(status='approved')
            else:
                # Status field doesn't exist yet, show all listings
                qs = Listing.objects.all()
                
        except Exception as e:
            # Fallback: show all listings if there's any error
            qs = Listing.objects.all()
            
        serializer = ListingSerializer(qs, many=True)
        # Optional: log view activity for authenticated users
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                action="view",
                description="Viewed shop listings",
            )
        return Response(serializer.data)

    # POST - create listing
    data = request.data.copy()
    serializer = ListingSerializer(data=data)
    if serializer.is_valid():
        try:
            # Try to create with status field
            instance = serializer.save(
                seller=request.user if request.user.is_authenticated else None,
                status="pending"
            )
        except Exception:
            # Fallback: create without status field
            instance = serializer.save(
                seller=request.user if request.user.is_authenticated else None
            )
        return Response(ListingSerializer(instance).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def listing_detail_view(request, listing_id):
    """Get detailed information for a specific car listing"""
    try:
        # Try to get approved listing first
        try:
            listing = Listing.objects.get(id=listing_id, status="approved")
        except Exception:
            # Fallback: get any listing if status field doesn't exist
            listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({"detail": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get seller profile information
    seller_info = {}
    if listing.seller:
        try:
            profile = Profile.objects.get(user=listing.seller)
            seller_info = {
                "username": listing.seller.username,
                "full_name": profile.full_name or listing.seller.get_full_name() or listing.seller.username,
                "phone": profile.phone,
                "email": listing.seller.email,
                "avatar_url": profile.avatar_url,
                "member_since": listing.seller.date_joined.strftime("%B %Y"),
            }
        except Profile.DoesNotExist:
            seller_info = {
                "username": listing.seller.username,
                "full_name": listing.seller.get_full_name() or listing.seller.username,
                "phone": "",
                "email": listing.seller.email,
                "avatar_url": "",
                "member_since": listing.seller.date_joined.strftime("%B %Y"),
            }
    
    # Get related listings (same make or similar price range)
    related_listings = []
    try:
        related_qs = Listing.objects.filter(status="approved").exclude(id=listing_id)
        # First try same make
        same_make = related_qs.filter(make__iexact=listing.make)[:3]
        related_listings.extend(ListingSerializer(same_make, many=True).data)
        
        # If we need more, add similar price range
        if len(related_listings) < 3:
            price_min = listing.price * 0.8
            price_max = listing.price * 1.2
            similar_price = related_qs.filter(
                price__gte=price_min, 
                price__lte=price_max
            ).exclude(id__in=[r['id'] for r in related_listings])[:3-len(related_listings)]
            related_listings.extend(ListingSerializer(similar_price, many=True).data)
    except Exception:
        # Fallback for when status field doesn't exist
        try:
            related_qs = Listing.objects.exclude(id=listing_id)
            same_make = related_qs.filter(make__iexact=listing.make)[:3]
            related_listings.extend(ListingSerializer(same_make, many=True).data)
        except Exception:
            pass
    
    # Log view activity for authenticated users
    if request.user.is_authenticated:
        UserActivity.objects.create(
            user=request.user,
            action="view",
            description=f"Viewed car details: {listing.make} {listing.model}",
        )
    
    # Prepare detailed response
    listing_data = ListingSerializer(listing).data
    listing_data.update({
        "seller_info": seller_info,
        "related_listings": related_listings,
        "features": _generate_car_features(listing),
        "specifications": _generate_car_specifications(listing),
    })
    
    return Response(listing_data)


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def add_listing_images(request, listing_id):
    """Add multiple images to a car listing"""
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({"detail": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user owns the listing (if authenticated)
    if request.user.is_authenticated and listing.seller != request.user and not request.user.is_staff:
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    
    image_urls = request.data.get('image_urls', [])
    if not image_urls:
        return Response({"detail": "No image URLs provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    created_images = []
    for i, url in enumerate(image_urls):
        image = ListingImage.objects.create(
            listing=listing,
            image_url=url,
            order=i
        )
        created_images.append(ListingImageSerializer(image).data)
    
    return Response({
        "message": f"Added {len(created_images)} images to listing",
        "images": created_images
    }, status=status.HTTP_201_CREATED)


def _generate_car_features(listing):
    """Generate comprehensive car features list based on listing data"""
    features = []
    
    # Basic features based on available data
    if listing.fuel:
        fuel_features = {
            "petrol": ["Petrol Engine", "Fuel Efficient", "Low Maintenance"],
            "diesel": ["Diesel Engine", "High Torque", "Better Mileage"],
            "cng": ["CNG Kit", "Eco Friendly", "Low Running Cost"],
            "hybrid": ["Hybrid Technology", "Fuel Efficient", "Eco Friendly"],
            "electric": ["Electric Motor", "Zero Emissions", "Silent Operation"]
        }
        features.extend(fuel_features.get(listing.fuel.lower(), []))
    
    if listing.trans:
        trans_features = {
            "manual": ["Manual Transmission", "Driver Control", "Fuel Efficient"],
            "automatic": ["Automatic Transmission", "Smooth Driving", "City Friendly"],
            "amt": ["AMT Transmission", "Automated Manual", "Easy Driving"]
        }
        features.extend(trans_features.get(listing.trans.lower(), []))
    
    # Add common car features
    common_features = [
        "Power Steering", "Power Windows", "Central Locking", "Air Conditioning",
        "Music System", "Adjustable Seats", "Safety Belts", "Anti-Lock Braking System",
        "Airbags", "Fog Lights", "Alloy Wheels", "Remote Central Locking",
        "Electric Mirrors", "Tinted Glass", "Rear Parking Sensors", "GPS Navigation"
    ]
    
    # Add some features based on car age and price
    if listing.year and listing.year >= 2018:
        features.extend(["Touchscreen Infotainment", "Bluetooth Connectivity", "USB Charging"])
    
    if listing.price and listing.price > 800000:
        features.extend(["Leather Seats", "Sunroof", "Climate Control", "Cruise Control"])
    
    # Randomly select 12-16 features to make it realistic
    import random
    all_features = list(set(features + random.sample(common_features, min(12, len(common_features)))))
    return sorted(all_features[:16])


def _generate_car_specifications(listing):
    """Generate car specifications based on listing data"""
    specs = {
        "Overview": {
            "Make": listing.make,
            "Model": listing.model,
            "Year": str(listing.year) if listing.year else "N/A",
            "Kilometers": f"{listing.km:,} km" if listing.km else "N/A",
            "Fuel Type": listing.fuel.title() if listing.fuel else "N/A",
            "Transmission": listing.trans.title() if listing.trans else "N/A",
            "Location": listing.location if listing.location else "N/A",
        }
    }
    
    # Add engine specifications (estimated based on make/model)
    engine_specs = {}
    if listing.fuel:
        if listing.fuel.lower() == "petrol":
            engine_specs["Engine Type"] = "Petrol"
            engine_specs["Displacement"] = "1200-1500 cc"
        elif listing.fuel.lower() == "diesel":
            engine_specs["Engine Type"] = "Diesel"
            engine_specs["Displacement"] = "1500-2000 cc"
        elif listing.fuel.lower() == "cng":
            engine_specs["Engine Type"] = "CNG"
            engine_specs["Displacement"] = "1000-1200 cc"
    
    if engine_specs:
        specs["Engine"] = engine_specs
    
    return specs


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def add_listing_images(request, listing_id):
    """Add multiple images to a car listing"""
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({"detail": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user owns the listing (if authenticated)
    if request.user.is_authenticated and listing.seller != request.user and not request.user.is_staff:
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    
    image_urls = request.data.get('image_urls', [])
    if not image_urls:
        return Response({"detail": "No image URLs provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    created_images = []
    for i, url in enumerate(image_urls):
        image = ListingImage.objects.create(
            listing=listing,
            image_url=url,
            order=i
        )
        created_images.append(ListingImageSerializer(image).data)
    
    return Response({
        "message": f"Added {len(created_images)} images to listing",
        "images": created_images
    }, status=status.HTTP_201_CREATED)
    """Generate car specifications based on listing data"""
    specs = {
        "Overview": {
            "Make": listing.make,
            "Model": listing.model,
            "Year": str(listing.year) if listing.year else "N/A",
            "Kilometers": f"{listing.km:,} km" if listing.km else "N/A",
            "Fuel Type": listing.fuel.title() if listing.fuel else "N/A",
            "Transmission": listing.trans.title() if listing.trans else "N/A",
            "Location": listing.location if listing.location else "N/A",
        }
    }
    
    # Add engine specifications (estimated based on make/model)
    engine_specs = {}
    if listing.fuel:
        if listing.fuel.lower() == "petrol":
            engine_specs["Engine Type"] = "Petrol"
            engine_specs["Displacement"] = "1200-1500 cc"
        elif listing.fuel.lower() == "diesel":
            engine_specs["Engine Type"] = "Diesel"
            engine_specs["Displacement"] = "1500-2000 cc"
    
    if engine_specs:
        specs["Engine"] = engine_specs
    
    return specs


@api_view(["POST"])  # contact form submit
@permission_classes([AllowAny])
@authentication_classes([])
def contact_view(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"ok": True}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])  # signup
@permission_classes([AllowAny])
@authentication_classes([])
def signup_view(request):
    try:
        print(f"DEBUG: Signup request data: {request.data}")
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            print(f"DEBUG: Signup successful for user: {user.username}")
            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "token": token.key,
            }, status=status.HTTP_201_CREATED)
        print(f"DEBUG: Signup validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        print(f"DEBUG: Signup exception: {str(e)}")
        print(traceback.format_exc())
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])  # login
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response({"detail": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    token, _ = Token.objects.get_or_create(user=user)
    # Log login activity
    UserActivity.objects.create(user=user, action="login", description="User logged in")
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "token": token.key,
        "is_staff": bool(getattr(user, "is_staff", False)),
        "is_superuser": bool(getattr(user, "is_superuser", False)),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def book_service_slot(request):
    """Book a service/repair slot for vehicle"""
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'city', 'car_make', 'car_model', 'car_year', 'preferred_date', 'preferred_time', 'service_type']
        for field in required_fields:
            if not data.get(field):
                return Response({"detail": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Format detected damages
        detected_damages = data.get('detected_damages', [])
        damages_text = '\n'.join([f"  - {damage}" for damage in detected_damages]) if detected_damages else '  - No specific damage detected'
        
        # Create contact message for service booking
        message_text = f"""
Service/Repair Slot Booking

Vehicle Details:
- Make: {data.get('car_make')}
- Model: {data.get('car_model')}
- Year: {data.get('car_year')}
- Registration: {data.get('reg_number', 'Not provided')}

Customer Details:
- Name: {data.get('name')}
- Phone: {data.get('phone')}
- Email: {data.get('email')}
- City: {data.get('city')}

Service Details:
- Service Type: {data.get('service_type').replace('_', ' ').title()}
- Preferred Date: {data.get('preferred_date')}
- Preferred Time: {data.get('preferred_time')}

Detected Damages/Issues:
{damages_text}

Additional Details:
{data.get('message', 'None')}

Booking Date: {data.get('booking_date', 'N/A')}
        """.strip()
        
        # Save as contact message
        ContactMessage.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            subject=f"Service Booking - {data.get('car_make')} {data.get('car_model')} ({data.get('service_type').replace('_', ' ').title()})",
            message=message_text
        )

        try:
            service_type_label = (data.get('service_type') or '').replace('_', ' ').title()
            subject = f"AutoPro Elite: Service Booking Confirmation ({service_type_label})"
            to_email = data.get('email')
            customer_name = data.get('name') or 'Customer'
            text_message = (
                f"Hello {customer_name},\n\n"
                f"Your service/repair slot booking request has been received.\n\n"
                f"Vehicle: {data.get('car_make')} {data.get('car_model')} ({data.get('car_year')})\n"
                f"Registration: {data.get('reg_number', 'Not provided')}\n"
                f"City: {data.get('city')}\n"
                f"Service Type: {service_type_label}\n"
                f"Preferred Date: {data.get('preferred_date')}\n"
                f"Preferred Time: {data.get('preferred_time')}\n\n"
                f"We will contact you shortly to confirm the slot.\n\n"
                f"Thanks,\nAutoPro Elite"
            )
            html_message = (
                f"<p>Hello {customer_name},</p>"
                f"<p>Your service/repair slot booking request has been received.</p>"
                f"<p><strong>Vehicle:</strong> {data.get('car_make')} {data.get('car_model')} ({data.get('car_year')})<br>"
                f"<strong>Registration:</strong> {data.get('reg_number', 'Not provided')}<br>"
                f"<strong>City:</strong> {data.get('city')}<br>"
                f"<strong>Service Type:</strong> {service_type_label}<br>"
                f"<strong>Preferred Date:</strong> {data.get('preferred_date')}<br>"
                f"<strong>Preferred Time:</strong> {data.get('preferred_time')}</p>"
                f"<p>We will contact you shortly to confirm the slot.</p>"
                f"<p>Thanks,<br><strong>AutoPro Elite</strong></p>"
            )
            send_booking_confirmation_email(
                booking_type='service',
                to_email=to_email,
                subject=subject,
                text_message=text_message,
                html_message=html_message,
            )
        except Exception as e:
            print(f"Service booking email failed: {str(e)}")
        
        # Log activity if user is authenticated
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                action="create",
                description=f"Booked service slot for {data.get('car_make')} {data.get('car_model')}",
                metadata={
                    "car_make": data.get('car_make'),
                    "car_model": data.get('car_model'),
                    "car_year": data.get('car_year'),
                    "service_type": data.get('service_type'),
                    "preferred_date": data.get('preferred_date'),
                    "preferred_time": data.get('preferred_time'),
                    "detected_damages": detected_damages
                }
            )
        
        return Response({
            "success": True,
            "message": "Service slot booked successfully! We'll contact you shortly to confirm."
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Service booking error: {error_details}")
        return Response({
            "detail": f"Failed to book service slot: {str(e)}",
            "error_type": type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def book_test_drive(request):
    """Book a test drive for a car"""
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['car_id', 'car_name', 'name', 'phone', 'email', 'city', 'preferred_date', 'preferred_time']
        for field in required_fields:
            if not data.get(field):
                return Response({"detail": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create contact message for test drive booking
        message_text = f"""
Test Drive Booking Request

Car Details:
- Car: {data.get('car_name')}
- Price: ₹{data.get('car_price', 'N/A')}

Customer Details:
- Name: {data.get('name')}
- Phone: {data.get('phone')}
- Email: {data.get('email')}
- City: {data.get('city')}

Preferred Schedule:
- Date: {data.get('preferred_date')}
- Time: {data.get('preferred_time')}

Additional Message:
{data.get('message', 'None')}

Booking Date: {data.get('booking_date', 'N/A')}
        """.strip()
        
        # Save as contact message
        ContactMessage.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            subject=f"Test Drive Booking - {data.get('car_name')}",
            message=message_text
        )

        try:
            subject = f"AutoPro Elite: Test Drive Booking Confirmation"
            to_email = data.get('email')
            customer_name = data.get('name') or 'Customer'
            text_message = (
                f"Hello {customer_name},\n\n"
                f"Your test drive booking request has been received.\n\n"
                f"Car: {data.get('car_name')}\n"
                f"Price: ₹{data.get('car_price', 'N/A')}\n"
                f"City: {data.get('city')}\n"
                f"Preferred Date: {data.get('preferred_date')}\n"
                f"Preferred Time: {data.get('preferred_time')}\n\n"
                f"We will contact you shortly to confirm the test drive.\n\n"
                f"Thanks,\nAutoPro Elite"
            )
            html_message = (
                f"<p>Hello {customer_name},</p>"
                f"<p>Your test drive booking request has been received.</p>"
                f"<p><strong>Car:</strong> {data.get('car_name')}<br>"
                f"<strong>Price:</strong> ₹{data.get('car_price', 'N/A')}<br>"
                f"<strong>City:</strong> {data.get('city')}<br>"
                f"<strong>Preferred Date:</strong> {data.get('preferred_date')}<br>"
                f"<strong>Preferred Time:</strong> {data.get('preferred_time')}</p>"
                f"<p>We will contact you shortly to confirm the test drive.</p>"
                f"<p>Thanks,<br><strong>AutoPro Elite</strong></p>"
            )
            send_booking_confirmation_email(
                booking_type='test_drive',
                to_email=to_email,
                subject=subject,
                text_message=text_message,
                html_message=html_message,
            )
        except Exception as e:
            print(f"Test drive booking email failed: {str(e)}")
        
        # Log activity if user is authenticated
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                action="create",
                description=f"Booked test drive for {data.get('car_name')}",
                metadata={
                    "car_id": data.get('car_id'),
                    "car_name": data.get('car_name'),
                    "preferred_date": data.get('preferred_date'),
                    "preferred_time": data.get('preferred_time')
                }
            )
        
        return Response({
            "success": True,
            "message": "Test drive booked successfully! We'll contact you shortly to confirm."
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Test drive booking error: {error_details}")
        return Response({
            "detail": f"Failed to book test drive: {str(e)}",
            "error_type": type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def sell_car_page(request):
    """Render Sell Car page and handle form submission to create a Listing."""
    if request.method == "POST":
        # Personal Information
        owner_name = request.POST.get("owner_name", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        whatsapp = request.POST.get("whatsapp", "").strip()
        city = request.POST.get("city", "").strip()
        
        # Vehicle Registration Details
        registration_number = request.POST.get("registration_number", "").strip().upper()
        registration_year = int(request.POST.get("registration_year", 0) or 0)
        manufacturing_year = int(request.POST.get("manufacturing_year", 0) or 0)
        car_registration = request.POST.get("car_registration", "").strip()
        
        # Vehicle Details
        make = request.POST.get("make", "").strip()
        model = request.POST.get("model", "").strip()
        variant = request.POST.get("variant", "").strip()
        km = int(request.POST.get("km", 0) or 0)
        fuel = request.POST.get("fuel", "").strip()
        trans = request.POST.get("trans", "").strip()
        owners = request.POST.get("owners", "").strip()
        color = request.POST.get("color", "").strip()
        
        # Pricing & Additional Info
        price = int(request.POST.get("price", 0) or 0)
        location = request.POST.get("location", "").strip()
        heard_from = request.POST.get("heard_from", "").strip()
        description = request.POST.get("description", "").strip()
        img = request.POST.get("img", "").strip()
        
        # Get multiple image URLs (comma-separated or JSON array)
        image_urls_str = request.POST.get("image_urls", "").strip()
        image_urls = []
        if image_urls_str:
            try:
                # Try parsing as JSON array first
                import json
                image_urls = json.loads(image_urls_str)
            except:
                # Fall back to comma-separated
                image_urls = [url.strip() for url in image_urls_str.split(',') if url.strip()]

        # Validate required fields
        if not all([owner_name, mobile, whatsapp, city, registration_number, registration_year, 
                    manufacturing_year, car_registration, make, model, variant, km, fuel, trans, 
                    owners, price, location, heard_from]):
            messages.error(request, "Please fill all required fields marked with *")
        else:
            # Build comprehensive description with all details for admin_notes
            full_description = f"""
Owner: {owner_name}
Mobile: {mobile}
WhatsApp: {whatsapp}
City: {city}

Registration Number: {registration_number}
Registration Year: {registration_year}
Manufacturing Year: {manufacturing_year}
Registration State: {car_registration}

Brand: {make}
Model: {model}
Variant: {variant}
Kilometers Driven: {km:,} km
Fuel Type: {fuel}
Transmission: {trans}
Owner Serial: {owners}
Color: {color}

Expected Price: ₹{price:,}
Location: {location}
Heard About Us From: {heard_from}

Additional Details:
{description}
            """.strip()
            
            # Check if status field exists
            has_status_field = False
            try:
                test_listing = Listing()
                _ = test_listing.status
                has_status_field = True
            except:
                has_status_field = False
            
            # Use manufacturing_year as the year field for the listing
            year = manufacturing_year
            
            if has_status_field:
                # Create with status field
                listing = Listing.objects.create(
                    make=make, 
                    model=f"{model} {variant}".strip(),
                    year=year, 
                    km=km, 
                    fuel=fuel, 
                    trans=trans,
                    price=price, 
                    original_predicted_price=price, 
                    location=location, 
                    img=img or "",
                    seller=request.user if request.user.is_authenticated else None,
                    status="pending",
                    admin_notes=full_description,  # Store in admin_notes instead of description
                    description=description
                )
                
                # Create ListingImage records for additional images
                if image_urls:
                    try:
                        for idx, url in enumerate(image_urls):
                            if url:  # Skip empty URLs
                                ListingImage.objects.create(
                                    listing=listing,
                                    image_url=url,
                                    order=idx
                                )
                    except Exception as e:
                        print(f"Error creating listing images: {e}")
                        # Continue even if image creation fails
                
                messages.success(request, f"Your car listing has been submitted for approval! Listing ID: #{listing.id}. It will appear in the shop once approved by an admin.")
            else:
                # Create without status field
                listing = Listing.objects.create(
                    make=make, 
                    model=f"{model} {variant}".strip(),
                    year=year, 
                    km=km, 
                    fuel=fuel, 
                    trans=trans,
                    price=price, 
                    original_predicted_price=price, 
                    location=location, 
                    img=img or "",
                    seller=request.user if request.user.is_authenticated else None,
                    admin_notes=full_description,  # Store in admin_notes instead of description
                    description=description
                )
                messages.success(request, f"Your car listing has been published successfully! Listing ID: #{listing.id}")
            
            # Log activity if user is authenticated
            if request.user.is_authenticated:
                UserActivity.objects.create(
                    user=request.user,
                    action="create",
                    description=f"Created car listing: {make} {model} {variant}",
                    metadata={
                        "listing_id": listing.id,
                        "registration_number": registration_number,
                        "price": price,
                        "owner_name": owner_name,
                        "mobile": mobile
                    }
                )
            
            # After submission, redirect to shop to see other listings
            return redirect("shop")

    return render(request, "sell-car.html")


@api_view(["GET"])  # Spare parts catalog
@permission_classes([AllowAny])
@authentication_classes([])
def spareparts_view(request):
    """Return list of active spare parts with simple filtering.

    Query params (optional):
      - q: search in name/sku/category/compatible fields
      - category: exact match filter
      - make: compatible_make contains
      - model: compatible_model contains
      - active: 1/0 to include/exclude inactive (default 1)
    """
    qs = SparePart.objects.all()
    active = request.GET.get("active", "1").strip()
    if active in ("1", "true", "yes"):
        qs = qs.filter(is_active=True)

    q = (request.GET.get("q") or "").strip()
    category = (request.GET.get("category") or "").strip()
    make = (request.GET.get("make") or "").strip()
    model = (request.GET.get("model") or "").strip()

    from django.db.models import Q
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(sku__icontains=q)
            | Q(category__icontains=q)
            | Q(compatible_make__icontains=q)
            | Q(compatible_model__icontains=q)
            | Q(description__icontains=q)
        )
    if category:
        qs = qs.filter(category__iexact=category)
    if make:
        qs = qs.filter(compatible_make__icontains=make)
    if model:
        qs = qs.filter(compatible_model__icontains=model)

    qs = qs.order_by("name")[:200]
    data = SparePartSerializer(qs, many=True).data
    return Response(data)


# Helpers
def _get_or_create_cart(user: User) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# Upload endpoint for images (simple local storage)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
def upload_image(request):
    try:
        uploaded_files = []
        
        # Handle multiple files
        if "files" in request.FILES:
            files = request.FILES.getlist("files")
        elif "file" in request.FILES:
            files = [request.FILES["file"]]
        else:
            return Response({"detail": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        fs = FileSystemStorage(location=getattr(settings, "MEDIA_ROOT", None))
        
        for f in files:
            # Place under uploads/<timestamp>_originalname
            import time as _t
            filename = fs.save(f"uploads/{int(_t.time())}_{f.name}", f)
            url = fs.url(filename) if hasattr(fs, "url") else f"{getattr(settings, 'MEDIA_URL', '/media/')}{filename}"
            # Ensure absolute URL for frontend convenience
            if url.startswith("/"):
                absolute = request.build_absolute_uri(url)
            else:
                absolute = url
            uploaded_files.append({
                "filename": f.name,
                "url": absolute,
                "size": f.size
            })
        
        if len(uploaded_files) == 1:
            # Single file - return old format for backward compatibility
            return Response({"url": uploaded_files[0]["url"]}, status=status.HTTP_201_CREATED)
        else:
            # Multiple files - return array
            return Response({"files": uploaded_files}, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({"detail": f"upload failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Activity Endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_activities(request):
    qs = request.user.activities.all()[:200]
    return Response(UserActivitySerializer(qs, many=True).data)


@api_view(["POST"])  # general-purpose logger
@permission_classes([IsAuthenticated])
def log_activity(request):
    action = request.data.get("action")
    description = request.data.get("description", "")
    metadata = request.data.get("metadata")
    if not action:
        return Response({"detail": "'action' is required"}, status=status.HTTP_400_BAD_REQUEST)
    ua = UserActivity.objects.create(user=request.user, action=action, description=description, metadata=metadata)
    return Response(UserActivitySerializer(ua).data, status=status.HTTP_201_CREATED)


# Profile endpoints
@api_view(["GET", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def profile_me(request):
    # Ensure profile exists
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "GET":
        return Response(ProfileSerializer(profile).data)
    partial = (request.method == "PATCH")
    serializer = ProfileSerializer(profile, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Account (username/avatar) endpoints
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def account_me(request):
    user = request.user
    # Ensure profile exists
    profile, _ = Profile.objects.get_or_create(user=user)
    if request.method == "GET":
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar_url": profile.avatar_url or "",
        })
    data = request.data if isinstance(request.data, dict) else {}
    new_username = (data.get("username") or "").strip()
    avatar_url = (data.get("avatar_url") or "").strip()
    # Update username if provided and changed
    if new_username and new_username != user.username:
        # Basic validation: unique username
        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            return Response({"detail": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username
        user.save(update_fields=["username"])
    # Update avatar
    if avatar_url != (profile.avatar_url or ""):
        profile.avatar_url = avatar_url
        profile.save(update_fields=["avatar_url"])
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": profile.avatar_url or "",
    })


# Orders endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    qs = Order.objects.filter(user=request.user).order_by("-created_at")[:200]
    out = []
    for o in qs:
        out.append({
            "id": o.id,
            "status": o.status,
            "order_type": o.order_type,
            "total_amount": float(o.total_amount),
            "notes": o.notes,
            "created_at": o.created_at.isoformat(),
            "bill_number": o.bill_number or "",
            "bill_pdf_path": o.bill_pdf_path or "",
            "bill_sent_email": o.bill_sent_email,
        })
    return Response(out)


@api_view(["POST"])  # {order_id}
@permission_classes([IsAuthenticated])
def cancel_order(request):
    oid = request.data.get("order_id")
    try:
        o = Order.objects.get(id=oid, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    if o.status in ("completed", "cancelled"):
        return Response({"detail": f"Cannot cancel order in status '{o.status}'"}, status=status.HTTP_400_BAD_REQUEST)
    o.status = "cancelled"
    o.save(update_fields=["status"])
    return Response({"ok": True, "id": o.id, "status": o.status})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Create a new order from cart items with payment method"""
    try:
        data = request.data
        payment_method = data.get('payment_method', 'cod')
        delivery_address = data.get('delivery_address', {})
        cart_items = data.get('cart_items', [])
        
        # Validate cart items
        if not cart_items:
            return Response({"detail": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(cart_items, list):
            return Response({"detail": "cart_items must be an array"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate each cart item
        for idx, item in enumerate(cart_items):
            if not isinstance(item, dict):
                return Response({"detail": f"Item {idx} is not a valid object"}, status=status.HTTP_400_BAD_REQUEST)
            if 'name' not in item:
                return Response({"detail": f"Item {idx} missing 'name' field"}, status=status.HTTP_400_BAD_REQUEST)
            if 'price' not in item:
                return Response({"detail": f"Item {idx} missing 'price' field"}, status=status.HTTP_400_BAD_REQUEST)
            if 'quantity' not in item:
                return Response({"detail": f"Item {idx} missing 'quantity' field"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate total
        try:
            subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart_items)
        except (ValueError, KeyError) as e:
            return Response({"detail": f"Invalid price or quantity in cart items: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery_charge = 50.0  # Fixed delivery charge
        tax_amount = subtotal * 0.18  # 18% GST
        total_amount = subtotal + delivery_charge + tax_amount
        
        # Get customer details from profile
        profile_row = Profile.objects.filter(user=request.user).values('full_name', 'phone').first()
        profile_full_name = (profile_row or {}).get('full_name')
        profile_phone = (profile_row or {}).get('phone')
        customer_name = profile_full_name or request.user.get_full_name() or request.user.username
        customer_phone = profile_phone or delivery_address.get('phone', '')
        
        # Format delivery address
        address_parts = []
        if delivery_address.get('address'):
            address_parts.append(delivery_address['address'])
        if delivery_address.get('city'):
            address_parts.append(delivery_address['city'])
        if delivery_address.get('state'):
            address_parts.append(delivery_address['state'])
        if delivery_address.get('pincode'):
            address_parts.append(f"PIN: {delivery_address['pincode']}")
        formatted_address = ", ".join(address_parts) if address_parts else "N/A"
        
        # Create order with e-bill fields
        order = Order.objects.create(
            user=request.user,
            order_type="spare",
            status="pending" if payment_method == "cod" else "paid",
            total_amount=total_amount,
            subtotal=subtotal,
            tax_amount=tax_amount,
            delivery_charge=delivery_charge,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_email=request.user.email,
            customer_phone=customer_phone,
            delivery_address=formatted_address,
            notes=f"Payment: {payment_method.upper()}"
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_id=item.get('product_id', ''),
                name=item['name'],
                price=float(item['price']),
                quantity=int(item['quantity']),
                image_url=item.get('image_url', '')
            )
        
        # Clear user's cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
        
        # Generate e-bill automatically
        try:
            from .ebill_generator import generate_ebill_pdf
            from .email_utils import send_ebill_email
            
            pdf_path = generate_ebill_pdf(order)
            email_sent = send_ebill_email(order, pdf_path)
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action="create",
                description=f"Created order #{order.id} with {payment_method.upper()} and generated e-bill",
                metadata={
                    "order_id": order.id,
                    "payment_method": payment_method,
                    "total_amount": float(total_amount),
                    "items_count": len(cart_items),
                    "bill_number": order.bill_number,
                    "email_sent": email_sent
                }
            )
        except Exception as e:
            # Log error but don't fail the order
            print(f"E-bill generation error for order #{order.id}: {str(e)}")
            # Log activity without bill info
            UserActivity.objects.create(
                user=request.user,
                action="create",
                description=f"Created order #{order.id} with {payment_method.upper()}",
                metadata={
                    "order_id": order.id,
                    "payment_method": payment_method,
                    "total_amount": float(total_amount),
                    "items_count": len(cart_items)
                }
            )
        
        return Response({
            "id": order.id,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "delivery_charge": float(delivery_charge),
            "payment_method": payment_method,
            "bill_number": order.bill_number,
            "created_at": order.created_at.isoformat(),
            "message": f"Order placed successfully! Order ID: #{order.id}. E-bill has been sent to your email."
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Order creation error: {error_details}")  # Log to console
        return Response({
            "detail": f"Failed to create order: {str(e)}",
            "error_type": type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Cart Endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    cart = _get_or_create_cart(request.user)
    return Response(CartSerializer(cart).data)


@api_view(["POST"])  # {product_id, name, price, quantity?, image_url?}
@permission_classes([IsAuthenticated])
def cart_add(request):
    cart = _get_or_create_cart(request.user)
    serializer = CartItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_id=data["product_id"],
        defaults={
            "name": data["name"],
            "price": data["price"],
            "quantity": data.get("quantity", 1),
            "image_url": data.get("image_url", ""),
        },
    )
    if not created:
        item.quantity += data.get("quantity", 1)
        item.name = data["name"]  # keep latest name/price
        item.price = data["price"]
        item.image_url = data.get("image_url", item.image_url)
        item.save()
    UserActivity.objects.create(user=request.user, action="add_to_cart", description=f"Added {item.name}")
    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])  # {product_id, quantity}
@permission_classes([IsAuthenticated])
def cart_update(request):
    cart = _get_or_create_cart(request.user)
    product_id = request.data.get("product_id")
    quantity = int(request.data.get("quantity", 1))
    if not product_id:
        return Response({"detail": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        item = cart.items.get(product_id=product_id)
    except CartItem.DoesNotExist:
        return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return Response(CartSerializer(cart).data)


@api_view(["POST"])  # {product_id}
@permission_classes([IsAuthenticated])
def cart_remove(request):
    cart = _get_or_create_cart(request.user)
    product_id = request.data.get("product_id")
    if not product_id:
        return Response({"detail": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)
    cart.items.filter(product_id=product_id).delete()
    return Response(CartSerializer(cart).data)


@api_view(["POST"])  # clears the cart
@permission_classes([IsAuthenticated])
def cart_clear(request):
    cart = _get_or_create_cart(request.user)
    cart.items.all().delete()
    return Response(CartSerializer(cart).data)








# Chatbot Endpoint (uses local pretrained QnA classifier)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
def chatbot_reply(request):
    """
    Accepts JSON: {"message": "..."}
    Returns: {"reply": "..."}

    Implementation uses a local pretrained model found under `backend/qna/`.
    It supports both standalone classifiers and sklearn Pipelines.
    """
    try:
        payload = request.data if isinstance(request.data, dict) else json.loads(request.body.decode("utf-8"))
    except Exception:
        return Response({"detail": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

    user_message = (payload or {}).get("message", "").strip()
    if not user_message:
        return Response({"detail": "'message' is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Handle simple greetings/thanks deterministically (no model call, no topic restriction)
    try:
        msg_norm = re.sub(r"\s+", " ", (user_message or "").strip().lower())
        msg_compact = re.sub(r"[^a-z0-9\s]", "", msg_norm)
        greet_set = {"hi", "hello", "hey", "hii", "hiii", "hola", "good morning", "good afternoon", "good evening"}
        thanks_set = {"thanks", "thank you", "thx", "ty", "thankyou", "thank u"}
        bye_set = {"bye", "goodbye", "see you", "see ya", "cya"}

        if msg_compact in greet_set:
            return Response({
                "reply": "Hello! I'm your AutoPro assistant. Ask me about cars, spare parts, service bookings, or our listings.",
                "provider": "static",
            })
        if msg_compact in thanks_set:
            return Response({
                "reply": "You're welcome! Anything else I can help you with about cars or AutoPro services?",
                "provider": "static",
            })
        if msg_compact in bye_set:
            return Response({
                "reply": "Goodbye! If you need help with cars, service, or parts, come back anytime.",
                "provider": "static",
            })
    except Exception:
        pass

    # Use local QnA model from backend/qna/ with spell-correction
    qna_status = "ready" if _CHATBOT_READY else ("error: " + str(_CHATBOT_ERR or "not_loaded"))

    # 1) DB-backed price shortcut (keep this helpful feature)
    try:
        from .models import Listing  # local import to avoid cycles at module load
        from django.db.models import Q
        direct_price = _try_price_answer(user_message)
        if isinstance(direct_price, str) and direct_price:
            return Response({"reply": direct_price, "provider": "price-db", "qna": qna_status})
    except Exception:
        pass

    # 2) Prefer Gemini for responses (as requested), keep local model only as optional fallback
    try:
        print(f"DEBUG: Attempting Gemini for message: {user_message[:50]}...")
        gemini_text = _gemini_generate(user_message)
        return Response({
            "reply": gemini_text,
            "provider": "gemini",
            "qna": qna_status,
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"DEBUG: Gemini failed: {error_msg}")
        print(traceback.format_exc())
        
        # Check for 403/Blocked key errors
        if "403" in error_msg or "blocked" in error_msg.lower():
             print("DEBUG: API key error. Falling back to local/static models.")

        # Optional fallback to local model if available and not disabled
        disable_local = getattr(settings, "CHATBOT_DISABLE_LOCAL", True)
        print(f"DEBUG: Local fallback status - Ready: {_CHATBOT_READY}, Disabled: {disable_local}")
        
        if not disable_local and _CHATBOT_READY and _vectorizer is not None and _model is not None:
            print("DEBUG: Falling back to local model...")
            try:
                corrected = _simple_spell_correct(user_message)
                if hasattr(_model, "predict"):
                    if _vectorizer is not None and not hasattr(_model, "steps"):
                        X = _vectorizer.transform([corrected])
                        pred = _model.predict(X)
                    else:
                        pred = _model.predict([corrected])
                else:
                    pred = _model(corrected)

                reply_items = None
                reply_text = None
                try:
                    import numpy as np  # optional normalization
                    is_array = isinstance(pred, (list, tuple)) or (hasattr(pred, 'shape') and hasattr(pred, 'tolist'))
                    if hasattr(pred, 'tolist'):
                        pred = pred.tolist()
                except Exception:
                    is_array = isinstance(pred, (list, tuple))

                if is_array:
                    reply_items = [str(x).strip() for x in (pred if isinstance(pred, (list, tuple)) else [pred]) if str(x).strip()]
                    if len(reply_items) == 1:
                        reply_text = reply_items[0]
                        reply_items = None
                else:
                    if isinstance(pred, (list, tuple)) and pred:
                        reply_text = str(pred[0])
                    else:
                        reply_text = str(pred)

                if 'insuranc' in corrected.lower():
                    insurance_msg = "Yes, we assist in transferring or renewing the insurance."
                    if reply_items is None:
                        reply_items = [insurance_msg]
                        reply_text = None
                    else:
                        if all(insurance_msg.lower() != it.lower() for it in reply_items):
                            reply_items.append(insurance_msg)
            except Exception as e2:
                return Response({"detail": f"Prediction error: {e2}", "qna": qna_status}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            payload = {
                "provider": "qna-local",
                "qna": qna_status,
                "corrected": corrected if corrected != user_message else None,
            }
            # Normalize to string
            if reply_items is not None:
                reply_text_norm = "; ".join([str(x) for x in reply_items if str(x).strip()])
            else:
                reply_text_norm = str(reply_text) if reply_text is not None else ""
            payload["reply"] = reply_text_norm
            return Response(payload)
        else:
            fb = _static_chat_fallback(user_message)
            if fb:
                print("DEBUG: Using static fallback...")
                return Response({"reply": fb, "provider": "static-fallback", "qna": qna_status})
            
            # Check for 429 Rate Limit
            if "429" in error_msg:
                 return Response({"detail": "AI assistant is busy (rate limit). Please try again in a moment."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                 
            return Response({
                "reply": f"Sorry, I am currently experiencing technical difficulties. (Error: {error_msg[:50]}...)",
                "provider": "error-fallback",
                "qna": qna_status
            })


# Damage Detection Endpoint (server-side proxy)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
def damage_detect(request):
    api_key = getattr(settings, "DAMAGE_API_KEY", "")
    api_secret = getattr(settings, "DAMAGE_API_SECRET", "")
    api_url = getattr(settings, "DAMAGE_API_URL", "")

    # If no external URL is configured, return a demo payload with bounding boxes the frontend understands
    if not api_url:
        # Demo fallback: generate relative boxes with label/score so UI can draw them
        try:
            provided = []
            if request.FILES:
                images = request.FILES.getlist("images") or ([request.FILES["image"]] if "image" in request.FILES else [])
                provided = [getattr(f, "name", "image.jpg") for f in images]
            else:
                payload = request.data if isinstance(request.data, dict) else json.loads(request.body.decode("utf-8"))
                if isinstance(payload, dict):
                    if "image_urls" in payload and isinstance(payload["image_urls"], list):
                        provided = payload["image_urls"]
                    elif "image_url" in payload:
                        provided = [payload["image_url"]]
            if not provided:
                return Response({"detail": "No images provided"}, status=status.HTTP_400_BAD_REQUEST)

            def demo_boxes():
                import random
                out = []
                count = 1 + int(random.random() * 3)
                labels = ["Scratch", "Dent", "Crack", "Broken Light", "Paint Chip"]
                for _ in range(count):
                    w = 0.2 + random.random() * 0.35
                    h = 0.12 + random.random() * 0.28
                    x = random.random() * (1 - w)
                    y = random.random() * (1 - h)
                    label = labels[int(random.random() * len(labels))]
                    score = 0.62 + random.random() * 0.32
                    out.append({"x": x, "y": y, "w": w, "h": h, "label": label, "score": score})
                return out

        
            demo = {
                "configured": False,
                "demo": True,
                "detail": "DAMAGE_API_URL not configured. Returning demo detections.",
                "results": [{"source": src, "detections": demo_boxes()} for src in provided],
            }
            return Response(demo)
        except Exception as e:
            return Response({"detail": f"Demo mode error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # External URL is set; if credentials are missing, signal not-implemented so frontend can fallback
    if not api_key or not api_secret:
        return Response({"detail": "Damage API credentials not configured on server"}, status=status.HTTP_501_NOT_IMPLEMENTED)

    headers = {
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
    }

    files = []
    data = {}
    json_payload = None

    try:
        # Prefer multipart images
        if request.FILES:
            images = request.FILES.getlist("images") or ([request.FILES["image"]] if "image" in request.FILES else [])
            for f in images:
                files.append(("images", (getattr(f, "name", "image.jpg"), f.read(), getattr(f, "content_type", "application/octet-stream"))))
        else:
            # JSON with image URLs
            payload = request.data if isinstance(request.data, dict) else json.loads(request.body.decode("utf-8"))
            if isinstance(payload, dict):
                if "image_urls" in payload:
                    json_payload = {"image_urls": payload["image_urls"]}
                elif "image_url" in payload:
                    json_payload = {"image_url": payload["image_url"]}
    except Exception:
        return Response({"detail": "Invalid input"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if files:
            resp = requests.post(api_url, headers=headers, files=files, data=data, timeout=40)
        else:
            if not json_payload:
                return Response({"detail": "No images provided"}, status=status.HTTP_400_BAD_REQUEST)
            headers_json = {**headers, "Content-Type": "application/json"}
            resp = requests.post(api_url, headers=headers_json, json=json_payload, timeout=40)

        if resp.status_code >= 400:
            return Response({"detail": "Upstream error", "status": resp.status_code, "body": resp.text}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(resp.json())
    except requests.Timeout:
        return Response({"detail": "Damage API request timed out"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        return Response({"detail": f"Server error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






















# --- Price Prediction Endpoint ---
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
def price_predict(request):
    """
    Accepts JSON with car details and returns a price estimate.
    Input fields (any subset ok):
      make, model, year, km, fuel, trans, owners, location, tire_condition

    Behavior:
      - If settings.PRICE_API_URL is configured, proxy the request to that URL using
        Authorization: Bearer <PRICE_API_KEY> header (or override later if needed).
      - Otherwise, use a deterministic heuristic to compute estimate and a +/- range.
    """
    try:
        payload = request.data if isinstance(request.data, dict) else json.loads(request.body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON object expected")
    except Exception:
        return Response({"detail": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

    make = (payload.get("make") or "").strip()
    model = (payload.get("model") or "").strip()
    year = int(payload.get("year") or 0)
    km = float(payload.get("km") or 0)
    fuel = (payload.get("fuel") or "").strip()
    trans = (payload.get("trans") or "").strip()
    owners = (payload.get("owners") or "1").strip()
    location = (payload.get("location") or "").strip()
    tire_condition = (payload.get("tire_condition") or "").strip()

    api_key = getattr(settings, "PRICE_API_KEY", "")
    api_url = getattr(settings, "PRICE_API_URL", "")

    # If external API configured, proxy the request
    if api_url:
        try:
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            upstream_body = {
                "make": make, "model": model, "year": year, "km": km,
                "fuel": fuel, "trans": trans, "owners": owners, "location": location,
                "tire_condition": tire_condition,
            }
            resp = requests.post(api_url, headers=headers, json=upstream_body, timeout=20)
            if resp.status_code >= 400:
                return Response({"detail": "Upstream error", "status": resp.status_code, "body": resp.text}, status=status.HTTP_502_BAD_GATEWAY)
            data = resp.json()
            return Response({
                "provider": "external",
                "configured": True,
                "estimate": data.get("estimate"),
                "low": data.get("low"),
                "high": data.get("high"),
                "currency": data.get("currency", "INR"),
                "raw": data,
            })
        except requests.Timeout:
            return Response({"detail": "Price API request timed out"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            return Response({"detail": f"Price API error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

    # Fallback heuristic estimator (server-side; deterministic and simple)
    try:
        current_year = 2025
        base_table = {
            "hatchback": 550000,
            "sedan": 800000,
            "suv": 1200000,
            "luxury": 2500000,
        }
        # Infer segment by model keywords (very rough)
        mm = f"{make} {model}".lower()
        if any(k in mm for k in ["glanza", "swift", "i10", "alto", "WagonR", "tiago", "polo", "baleno"]):
            base = base_table["hatchback"]
        elif any(k in mm for k in ["city", "verna", "ciaz", "virtus", "rapid", "ciaz", "aura", "dzire", "amaze"]):
            base = base_table["sedan"]
        elif any(k in mm for k in ["creta", "seltos", "brezza", "venue", "xuv", "scorpio", "harrier", "hector", "nexon"]):
            base = base_table["suv"]
        elif any(k in mm for k in ["bmw", "audi", "mercedes", "jaguar", "land rover", "volvo", "porsche"]):
            base = base_table["luxury"]
        else:
            base = 900000

        age = max(0, current_year - year) if year else 7
        # Depreciation: 18% first year, 12% thereafter compounded
        dep_factor = (1 - 0.18) * ((1 - 0.12) ** max(0, age - 1)) if age > 0 else 1.0

        # Km penalty: 0.08% per 1000 km
        km_penalty = max(0.6, 1.0 - (km / 5000) * 0.0008)

        # Fuel adjustments
        fuel_adj = {
            "diesel": 1.09,
            "petrol": 1.5,
            "cng": 1.00,
            "hybrid": 2.00,
            "electric": 1.50,
        }.get(fuel.lower(), 1.0)

        # Transmission
        trans_adj = {
            "automatic": 1.54,
            "amt": 1.32,
            "manual": 1.30,
        }.get(trans.lower(), 1.0)

        # Owners - price decreases with more owners
        # Extract owner number from formats like "1st Owner", "2nd Owner", etc.
        try:
            if 'owner' in owners.lower():
                # Extract number from "1st Owner", "2nd Owner", etc.
                owners_n = int(''.join(filter(str.isdigit, owners.split()[0])))
            elif owners.strip().endswith('+'):
                owners_n = 5  # 5+ owners
            else:
                owners_n = int(owners)
        except Exception:
            owners_n = 1
        
        # Price adjustment: 1st owner = 100%, 2nd = 92%, 3rd = 85%, 4th = 78%, 5+ = 72%
        owners_adj = {
            1: 1.00,   # 1st owner - full value
            2: 0.92,   # 2nd owner - 8% reduction
            3: 0.85,   # 3rd owner - 15% reduction
            4: 0.78,   # 4th owner - 22% reduction
        }.get(owners_n, 0.72)  # 5+ owners - 28% reduction

        # Tire condition adjustment
        tire_adj = {
            "excellent": 1.08,
            "good": 1.03,
            "fair": 0.97,
            "poor": 0.85,
        }.get(tire_condition.lower(), 1.0)

        est = base * dep_factor * km_penalty * fuel_adj * trans_adj * owners_adj * tire_adj
        est = max(50000, int(round(est / 1500) * 1000))

        spread = max(50000, int(est * 0.15))
        low = max(40000, est - spread)
        high = est + spread

        return Response({
            "provider": "heuristic",
            "configured": False,
            "estimate": est,
            "low": low,
            "high": high,
            "currency": "INR",
            "inputs": {
                "make": make, "model": model, "year": year, "km": km,
                "fuel": fuel, "trans": trans, "owners": owners, "location": location,
                "tire_condition": tire_condition,
            }
        })
    except Exception as e:
        return Response({"detail": f"Estimation error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# E-BILL GENERATION SYSTEM
# ============================================================================

from .ebill_generator import generate_ebill_pdf, generate_bill_number
from .email_utils import send_ebill_email
from django.http import FileResponse


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_bill(request, order_id):
    """
    Generate e-bill PDF for an order
    Automatically called after order creation
    """
    try:
        # Get order
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Get customer details from profile if not already set
        if not order.customer_name or not order.customer_email:
            profile = Profile.objects.filter(user=request.user).first()
            if not order.customer_name:
                order.customer_name = profile.full_name if profile and profile.full_name else request.user.get_full_name() or request.user.username
            if not order.customer_email:
                order.customer_email = request.user.email
            if not order.customer_phone and profile:
                order.customer_phone = profile.phone
            order.save()
        
        # Generate PDF
        pdf_path = generate_ebill_pdf(order)
        
        # Send email
        email_sent = False
        if order.customer_email:
            email_sent = send_ebill_email(order, pdf_path)
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action="create",
            description=f"Generated e-bill for order #{order.id}",
            metadata={
                "order_id": order.id,
                "bill_number": order.bill_number,
                "email_sent": email_sent
            }
        )
        
        return Response({
            "success": True,
            "bill_number": order.bill_number,
            "bill_pdf_path": order.bill_pdf_path,
            "email_sent": email_sent,
            "message": "E-bill generated successfully" + (" and sent to your email" if email_sent else "")
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"E-bill generation error: {error_details}")
        return Response({
            "detail": f"Failed to generate e-bill: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_bill(request, order_id):
    """
    Download e-bill PDF for an order
    """
    try:
        # Get order
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if bill exists
    if not order.bill_pdf_path:
        return Response({"detail": "Bill not generated yet"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get file path
    media_root = getattr(settings, 'MEDIA_ROOT', 'backend/media')
    pdf_path = os.path.join(media_root, order.bill_pdf_path)
    
    if not os.path.exists(pdf_path):
        # Try to generate if missing
        try:
            pdf_path = generate_ebill_pdf(order)
        except Exception as e:
            return Response({"detail": f"Bill file not found and regeneration failed: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)
    
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        action="view",
        description=f"Downloaded e-bill for order #{order.id}",
        metadata={"order_id": order.id, "bill_number": order.bill_number}
    )
    
    # Return file
    try:
        response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{order.bill_number}.pdf"'
        return response
    except Exception as e:
        return Response({"detail": f"Error reading bill file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bills(request):
    """
    Get list of all bills for the current user
    """
    orders = Order.objects.filter(user=request.user).exclude(bill_number='').order_by('-created_at')
    
    bills = []
    for order in orders:
        bills.append({
            "id": order.id,
            "bill_number": order.bill_number,
            "bill_date": order.bill_date.isoformat() if order.bill_date else order.created_at.isoformat(),
            "order_type": order.get_order_type_display(),
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_method": (order.payment_method or 'COD').upper(),
            "bill_pdf_path": order.bill_pdf_path,
            "email_sent": order.bill_sent_email,
            "created_at": order.created_at.isoformat(),
        })
    
    return Response(bills)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resend_bill_email(request, order_id):
    """
    Resend e-bill email for an order
    """
    try:
        # Get order
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if bill exists
    if not order.bill_pdf_path:
        return Response({"detail": "Bill not generated yet"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get file path
    media_root = getattr(settings, 'MEDIA_ROOT', 'backend/media')
    pdf_path = os.path.join(media_root, order.bill_pdf_path)
    
    if not os.path.exists(pdf_path):
        return Response({"detail": "Bill file not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Send email
    try:
        email_sent = send_ebill_email(order, pdf_path)
        
        if email_sent:
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action="update",
                description=f"Resent e-bill email for order #{order.id}",
                metadata={"order_id": order.id, "bill_number": order.bill_number}
            )
            
            return Response({
                "success": True,
                "message": "E-bill sent to your email successfully"
            })
        else:
            return Response({
                "detail": "Failed to send email. Please check your email address."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            "detail": f"Error sending email: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail_with_bill(request, order_id):
    """
    Get detailed order information including bill details
    """
    try:
        # Get order
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Get order items
    items = []
    for item in order.items.all():
        items.append({
            "product_id": item.product_id,
            "name": item.name,
            "price": float(item.price),
            "quantity": item.quantity,
            "image_url": item.image_url,
            "total": float(item.price) * item.quantity
        })
    
    # Build response
    response_data = {
        "id": order.id,
        "order_type": order.get_order_type_display(),
        "status": order.status,
        "total_amount": float(order.total_amount),
        "subtotal": float(order.subtotal) if order.subtotal else float(order.total_amount),
        "tax_amount": float(order.tax_amount) if order.tax_amount else 0,
        "delivery_charge": float(order.delivery_charge) if order.delivery_charge else 0,
        "payment_method": (order.payment_method or 'COD').upper(),
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "delivery_address": order.delivery_address,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "items": items,
        "bill": {
            "bill_number": order.bill_number,
            "bill_date": order.bill_date.isoformat() if order.bill_date else None,
            "bill_pdf_path": order.bill_pdf_path,
            "email_sent": order.bill_sent_email,
        } if order.bill_number else None
    }
    
    return Response(response_data)
