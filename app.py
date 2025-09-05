# -*- coding: utf-8 -*-

# AI Document Analyzer & Chat - Main Streamlit Application
# A NotebookLM-inspired document analysis tool with AI chat capabilities

import streamlit as st
import streamlit.components.v1
import time
import os
import json
import hashlib
from document_processor import DocumentProcessor
from vector_store import VectorStore
from ai_client import AIClient
from mindmap_generator import MindMapGenerator

# Optional plotly imports for mind map visualization
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError as e:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None
except Exception as e:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None

# PNG Icon Loading Function
import base64

def load_png_icons():
    """Load PNG icons and convert to base64 for embedding"""
    try:
        # Load gear icon for settings
        with open("attached_assets/gear_1756730569552.png", "rb") as f:
            gear_b64 = base64.b64encode(f.read()).decode()
            st.session_state.gear_icon_b64 = gear_b64
        
        # Load mind map icon
        with open("attached_assets/mind-map_1756730569553.png", "rb") as f:
            mindmap_b64 = base64.b64encode(f.read()).decode()
            st.session_state.mindmap_icon_b64 = mindmap_b64
            
        # Load process icon for logo
        with open("attached_assets/process_1756730569550.png", "rb") as f:
            process_b64 = base64.b64encode(f.read()).decode()
            st.session_state.process_icon_b64 = process_b64
            
    except Exception as e:
        st.error(f"Error loading PNG icons: {e}")

# SVG Icon Component Function
def get_svg_icon(icon_name, size=16, color="currentColor"):
    """Generate SVG icons to replace emojis"""
    icons = {
        "refresh": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>',
        "summary": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14,2 14,8 20,8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10,9 9,9 8,9"></polyline></svg>',
        "target": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
        "brain": f'<svg width="{size}" height="{size}" viewBox="0 0 512 512" fill="{color}"><path d="M0 0 C1.14491409 -0.00960754 2.28982819 -0.01921509 3.46943665 -0.02911377 C4.712108 -0.03336365 5.95477936 -0.03761353 7.23510742 -0.04199219 C9.14413094 -0.0505423 9.14413094 -0.0505423 11.09172058 -0.05926514 C13.78937356 -0.06872649 16.48691498 -0.07561733 19.18457031 -0.07910156 C22.63464051 -0.08457899 26.08431458 -0.10859039 29.53426075 -0.13707352 C32.83034623 -0.16022687 36.12645201 -0.16215173 39.42260742 -0.16699219 C41.27750542 -0.18551239 41.27750542 -0.18551239 43.1698761 -0.20440674 C44.32424667 -0.20140564 45.47861725 -0.19840454 46.66796875 -0.1953125 C47.68119705 -0.19895813 48.69442535 -0.20260376 49.73835754 -0.20635986 C54.0125808 0.35668823 56.64514298 2.06218195 59.32226562 5.39428711 C60.85429142 8.90966439 60.86832972 11.60059574 60.82104492 15.43066406 C60.81680008 16.11166672 60.81255524 16.79266937 60.80818176 17.49430847 C60.79148227 19.6544974 60.75384929 21.81372924 60.71557617 23.97363281 C60.70051792 25.4443224 60.68683151 26.91502671 60.67456055 28.38574219 C60.64160831 31.97784639 60.5898879 35.56939607 60.52807617 39.16113281 C61.71530273 39.49886719 62.9025293 39.83660156 64.12573242 40.18457031 C68.41205185 41.6025131 72.19488893 43.5281019 76.14916992 45.70019531 C94.59986926 55.59939833 109.93614371 58.78108262 130.91455078 58.12841797 C131.7912442 58.10589966 132.66793762 58.08338135 133.57119751 58.06018066 C135.21995231 58.00905034 136.8681825 57.93213805 138.51425171 57.82507324 C140.7421875 57.73974609 140.7421875 57.73974609 144.52807617 58.16113281 C147.44563296 60.86974293 148.40256353 62.28254431 148.96557617 66.22363281 C148.48181732 69.47172796 147.83396343 70.85524555 145.52807617 73.16113281 C141.89604628 74.37180944 138.57688268 74.28568857 134.79760742 74.25878906 C133.79957092 74.25727844 133.79957092 74.25727844 132.78137207 74.2557373 C130.30108918 74.25051387 127.82083091 74.23655259 125.34057617 74.22363281 C119.79245117 74.20300781 114.24432617 74.18238281 108.52807617 74.16113281 C108.52807617 90.16113281 108.52807617 106.16113281 108.52807617 122.16113281 C119.36140951 122.16113281 130.19474284 122.16113281 141.52807617 122.16113281 C141.52807617 118.86113281 141.52807617 115.56113281 141.52807617 112.16113281 C144.15274284 108.49446614 146.77740951 104.82779948 149.52807617 101.16113281 C155.8547428 93.82779948 161.8547428 93.82779948 172.52807617 95.16113281 C172.52807617 106.16113281 172.52807617 117.16113281 172.52807617 128.16113281 C177.19474284 128.16113281 181.8614095 128.16113281 186.52807617 128.16113281 C186.52807617 130.16113281 186.52807617 132.16113281 186.52807617 134.16113281 C184.19474284 136.49446614 181.8614095 138.82779948 179.52807617 141.16113281 C172.8614095 147.82779948 166.19474284 154.49446614 159.52807617 161.16113281 C151.52807617 161.16113281 143.52807617 161.16113281 135.52807617 161.16113281 C135.52807617 157.82779948 135.52807617 154.49446614 135.52807617 151.16113281 C132.19474284 148.49446614 128.8614095 145.82779948 125.52807617 143.16113281 C118.8614095 138.16113281 112.19474284 133.16113281 105.52807617 128.16113281 C101.8614095 128.16113281 98.19474284 128.16113281 94.52807617 128.16113281 C94.52807617 124.16113281 94.52807617 120.16113281 94.52807617 116.16113281 C97.8614095 111.16113281 101.19474284 106.16113281 104.52807617 101.16113281 C111.8614095 92.16113281 119.19474284 83.16113281 126.52807617 74.16113281"/><path d="M0 0 C1.73050598 -0.00430527 1.73050598 -0.00430527 3.49597168 -0.00869751 C5.93009941 -0.01073494 8.36424363 -0.00522765 10.79833984 0.00732422 C14.51827705 0.0233815 18.23712773 0.00746362 21.95703125 -0.01171875 C24.32552322 -0.00973626 26.69401453 -0.00589247 29.0625 0 C30.17202026 -0.00607269 31.28154053 -0.01214539 32.42468262 -0.0184021 C39.46749714 0.04555785 44.02919044 0.62130529 49.37084961 5.56274414 C51.55234018 9.28837463 51.62490531 12.56833412 51.59765625 16.76953125 C51.60385483 17.56948013 51.61005341 18.36942902 51.61643982 19.19361877 C51.62352316 20.88045031 51.62038988 22.56735197 51.60766602 24.25415039 C51.59380869 26.82504946 51.62787629 29.39229918 51.66601562 31.96289062 C51.66696703 33.60677172 51.66510684 35.25065734 51.66015625 36.89453125 C51.67341446 37.6572081 51.68667267 38.41988495 51.70033264 39.20567322 C51.63352755 43.06574065 51.22791202 45.67853074 48.86694336 48.80493164 C44.4580698 52.83725741 41.05604355 53.55101979 35.22729492 53.32397461 C33.32172407 53.19679732 31.4165435 53.06368334 29.51171875 52.92578125 C-2.84259344 51.21492718 -24.98810336 56.11210926 -52.96875 72.3984375 C-53.29875 78.9984375 -53.62875 85.5984375 -53.96875 92.3984375 C-43.40875 92.3984375 -32.84875 92.3984375 -21.96875 92.3984375 C-21.96875 89.4284375 -21.96875 86.4584375 -21.96875 83.3984375 C-20.26632689 78.55997183 -18.51417064 76.65384173 -13.96875 74.3984375 C-11.24391174 74.01075745 -11.24391174 74.01075745 -8.26391602 73.99438477 C-6.58175743 73.97535851 -6.58175743 73.97535851 -4.86561584 73.95594788 C-3.06235085 73.96035133 -3.06235085 73.96035133 -1.22265625 73.96484375 C0.64314842 73.95698097 0.64314842 73.95698097 2.54664612 73.94895935 C5.84720341 73.9408994 9.14734439 73.947998 12.44787598 73.95928955 C14.46554546 73.96093489 16.48265153 73.94895604 18.50024414 73.93188477 C22.38454507 73.90119482 26.26794094 73.89780279 30.15234375 73.90234375 C31.35249619 73.89110977 32.55264862 73.87987579 33.78916931 73.86830139 C40.13060761 73.82598193 46.47145605 73.82225621 52.8125 73.8203125 C54.01802826 73.81851807 55.22355652 73.81672364 56.46435547 73.81485748 C62.67932156 73.80639148 68.89389418 73.81779328 75.109375 73.83825684 C77.24390396 73.84581513 79.37840378 73.84828836 81.51293564 73.84646988 C87.0255596 73.83775029 92.53775616 73.84739946 98.05078125 73.86523438 C100.81732178 73.86731049 103.58384322 73.86475267 106.35040283 73.8581543 C111.21753717 73.84771931 116.08458662 73.85209923 120.95159912 73.86279297 C123.91732178 73.86731049 126.88384322 73.86475267 129.85040283 73.8581543 M129.85040283 73.8581543 C135.85040283 74.8581543 135.85040283 74.8581543 141.85040283 77.8581543 C145.85040283 80.8581543 145.85040283 80.8581543 148.85040283 85.8581543 C149.85040283 88.8581543 149.85040283 88.8581543 149.85040283 91.8581543 C148.85040283 93.8581543 148.85040283 93.8581543 147.85040283 95.8581543 C144.85040283 98.8581543 144.85040283 98.8581543 140.85040283 100.8581543 C136.85040283 101.8581543 136.85040283 101.8581543 132.85040283 101.8581543 C129.85040283 100.8581543 129.85040283 100.8581543 127.85040283 98.8581543 C125.85040283 95.8581543 125.85040283 95.8581543 125.85040283 91.8581543 C126.85040283 88.8581543 126.85040283 88.8581543 129.85040283 86.8581543 C132.85040283 85.8581543 132.85040283 85.8581543 136.85040283 85.8581543 C139.85040283 86.8581543 139.85040283 86.8581543 142.85040283 89.8581543 C143.85040283 91.8581543 143.85040283 91.8581543 143.85040283 93.8581543 C142.85040283 95.8581543 142.85040283 95.8581543 140.85040283 96.8581543"/></svg>',
        "chart": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        "search": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>',
        "chat": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>',
        "users": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
        "rocket": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"></path><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"></path></svg>',
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        "warning": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "explore": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>',
        "details": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14,2 14,8 20,8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>',
        "analyze": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m15.5-6.5-4.24 4.24M7.76 16.24 3.5 20.5m13-13L12.24 11.76M7.76 7.76 3.5 3.5"></path></svg>',
        "data": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>',
        "discuss": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1.5-2s-1.5.62-1.5 2a2.5 2.5 0 0 0 2.5 2.5z"></path><path d="M12 6c2.5 0 3.5 2.5 3.5 5s-1 5-3.5 5-3.5-2.5-3.5-5 1-5 3.5-5z"></path><path d="M3 19c0-8 5-8 9-8s9 0 9 8"></path></svg>',
        "settings": f'<svg width="{size}" height="{size}" viewBox="0 0 512 512" fill="{color}"><path d="M0 0 C9.30964522 7.56680992 14.938336 18.1747756 16.50390625 30.03515625 C17.69244586 43.79478794 13.00084573 54.30972779 5.19140625 65.28515625 C-3.19323865 73.86479289 -13.63389441 78.26985307 -25.49609375 79.03515625 C-25.65902168 80.16553062 -25.65902168 80.16553062 -25.82524109 81.31874084 C-27.15227719 90.25553997 -28.80344416 99.11224475 -30.578125 107.96875 C-30.72450598 108.69955339 -30.87088696 109.43035679 -31.02170372 110.18330574 C-31.79481297 114.03607502 -32.57270622 117.88784767 -33.35375977 121.73901367 C-33.99486553 124.90541972 -34.62549807 128.07364699 -35.24731445 131.24389648 C-36.00513193 135.10719722 -36.78070629 138.96653092 -37.56903648 142.82371712 C-37.8642177 144.28282819 -38.15326323 145.74319542 -38.43583107 147.20480156 C-41.227277 161.59416187 -41.227277 161.59416187 -46.49609375 166.03515625 C-49.99220652 167.70939721 -52.75414907 168.28381928 -56.61506653 168.27566528 C-57.62322418 168.27841461 -58.63138184 168.28116394 -59.67008972 168.28399658 C-60.76485123 168.27680603 -61.85961273 168.26961548 -62.98754883 168.26220703 C-64.72965637 168.26264511 -64.72965637 168.26264511 -66.50695801 168.26309204 C-70.34325651 168.26169945 -74.17936045 168.24614123 -78.015625 168.23046875 C-80.67649159 168.22673837 -83.33734742 168.22379312 -85.99821472 168.22189331 C-92.28441588 168.215683 -98.57054729 168.19927829 -104.85671777 168.17919433 C-112.71761615 168.15462564 -120.57852592 168.14369411 -128.43945312 168.1328125 C-142.45838764 168.11334645 -156.47716999 168.07327993 -170.49609375 168.03515625 C-170.49609375 187.83515625 -170.49609375 207.63515625 -170.49609375 228.03515625 C-118.68609375 227.70515625 -66.87609375 227.37515625 -13.49609375 227.03515625 C-11.51609375 223.07515625 -9.53609375 219.11515625 -7.49609375 215.03515625 C-0.40235263 205.10148097 8.55757486 199.22203726 20.31640625 196.34765625 C33.65953303 195.03950657 45.56024751 196.85970799 56.50390625 205.03515625 C64.9547491 212.20871881 71.3372371 221.13637086 72.78090477 233.03515625 M72.78090477 233.03515625 C73.80090477 248.43515625 73.80090477 248.43515625 69.50390625 265.03515625 C69.21226074 265.95515625 68.92061523 266.87515625 68.62109375 267.82421875 C65.69309711 274.92080078 61.70434569 280.83491211 55.50390625 286.03515625 C45.3625423 295.52423096 31.91049194 300.25589218 17.50390625 300.03515625 C3.14166565 299.51923065 -10.53395939 295.05053711 -20.49609375 284.03515625 C-32.14276123 270.60681152 -37.99682617 254.49786377 -37.49609375 236.03515625 C-35.99609375 222.03515625 -35.99609375 222.03515625 -29.49609375 210.03515625 C-27.49609375 206.03515625 -27.49609375 206.03515625 -25.49609375 202.03515625 C-18.64782715 189.41223145 -9.17095947 179.40374756 5.50390625 174.03515625 C20.16046143 170.58825684 35.85040283 171.85778809 49.50390625 179.03515625 C64.29559326 188.18386841 74.21002197 202.75854492 78.50390625 220.03515625 C79.02844238 222.26515625 79.55297852 224.49515625 80.08984375 226.79296875 C80.50390625 228.35515625 80.50390625 228.35515625 80.50390625 230.03515625 C80.12890625 232.03515625 80.12890625 232.03515625 79.75390625 234.03515625 C79.46226074 234.95515625 79.17061523 235.87515625 78.87109375 236.82421875 C76.58309711 243.92080078 73.59434569 249.83491211 68.50390625 254.03515625 C60.8625423 262.52423096 50.91049194 267.25589218 38.50390625 267.03515625 C25.14166565 266.51923065 12.46604061 262.05053711 3.50390625 251.03515625 C-6.14276123 239.60681152 -10.99682617 225.49786377 -10.49609375 209.03515625 C-9.49609375 198.03515625 -9.49609375 198.03515625 -4.49609375 189.03515625 C-2.49609375 185.03515625 -2.49609375 185.03515625 -0.49609375 181.03515625 C6.35217285 170.41223145 14.82904053 162.40374756 27.50390625 158.03515625 C38.16046143 155.58825684 49.85040283 156.85778809 61.50390625 162.03515625 C74.29559326 169.18386841 82.21002197 181.75854492 85.50390625 197.03515625 C85.88890625 199.03515625 85.88890625 199.03515625 86.27734375 201.11328125 C86.50390625 202.35515625 86.50390625 202.35515625 86.50390625 204.03515625 M86.50390625 204.03515625 C86.13890625 206.03515625 86.13890625 206.03515625 85.76953125 208.111328125"/><path d="M0 0 C0.87022797 -0.00671722 1.74045593 -0.01343445 2.63705444 -0.02035522 C5.51867354 -0.03937916 8.40006026 -0.04326167 11.28173828 -0.04541016 C13.28329566 -0.05183518 15.28485209 -0.05856332 17.28640747 -0.06558228 C21.48458026 -0.07756615 25.68267069 -0.08126197 29.88085938 -0.08007812 C35.2601913 -0.07987491 40.63899508 -0.10717498 46.01820183 -0.14162254 C50.15319239 -0.16386149 54.28805527 -0.16791658 58.42309952 -0.16685867 C60.40623927 -0.16921924 62.3893823 -0.17806835 64.37246323 -0.19352341 C67.14712227 -0.21312192 69.92063496 -0.2073695 72.6953125 -0.1953125 C73.92362793 -0.21217102 73.92362793 -0.21217102 75.17675781 -0.22937012 C79.04093486 -0.18670627 81.04030015 0.027167 84.42060852 2.06549072 C89.6574245 7.73163927 90.25519434 16.54539968 91.52001953 23.90771484 C91.78000481 25.37617355 91.78000481 25.37617355 92.04524231 26.8742981 C92.407144 28.92589018 92.76580091 30.97805708 93.12133789 33.03076172 C93.66681265 36.17858008 94.22245197 39.32447654 94.77978516 42.47021484 C95.13128594 44.47011135 95.4822178 46.47010796 95.83251953 48.47021484 C95.9980986 49.41081757 96.16367767 50.35142029 96.33427429 51.32052612 C96.48475723 52.19218414 96.63524017 53.06384216 96.7902832 53.96191406 C96.98988899 55.11033279 96.98988899 55.11033279 97.19352722 56.2819519 C97.47705078 58.29052734 97.47705078 58.29052734 97.47705078 61.29052734 C98.29278564 61.44400635 98.29278564 61.44400635 99.125 61.60058594 C104.9296865 62.77941057 110.17321855 64.56758716 115.60205078 66.91552734 C116.41810791 67.26599121 117.23416504 67.61645508 118.07495117 67.97753906 C123.42652774 70.31282931 128.71617469 72.75586282 133.91455078 75.41552734 C135.08888672 76.01623047 136.26322266 76.61693359 137.47314453 77.23583984 C141.4528059 79.95794892 143.97260268 82.87155966 144.97314453 87.66943359 C144.84902048 92.29512339 144.66910901 95.67286136 141.47705078 99.29052734 C137.51030564 102.12391673 134.12254273 102.85927823 129.27783203 102.12646484 C124.0832199 100.57607 118.00077462 98.26068425 114.07705688 94.2905273 C110.51030564 91.12391673 109.12254273 87.85927823 109.27783203 83.12646484 C109.08321999 79.57607 109.00077462 76.26068425 110.07705688 72.2905273 C112.51030564 67.12391673 116.12254273 63.85927823 121.27783203 62.12646484 C126.08321999 61.57607 130.00077462 62.26068425 134.07705688 64.2905273 M134.07705688 64.2905273 C140.51030564 67.12391673 145.12254273 71.85927823 147.27783203 79.12646484 C148.08321999 82.57607 148.00077462 85.26068425 147.07705688 88.2905273 C145.51030564 92.12391673 142.12254273 94.85927823 137.27783203 95.12646484 C132.08321999 94.57607 128.00077462 92.26068425 125.07705688 88.2905273 C123.51030564 85.12391673 123.12254273 81.85927823 124.27783203 78.12646484 C126.08321999 74.57607 129.00077462 72.26068425 133.07705688 71.2905273"/></svg>',
        "trash": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="3,6 5,6 21,6"></polyline><path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>',
        "robot": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>'
    }
    return icons.get(icon_name, f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>')

# Helper functions for caching and chat persistence
def load_cached_analyses():
    """Load cached analysis results from session state"""
    return {}

def save_cached_analyses(cache_data):
    """Save cached analysis results to session state"""
    if "cached_analyses" in st.session_state:
        st.session_state.cached_analyses = cache_data

def load_chat_history():
    """Load chat history from persistent storage"""
    try:
        if os.path.exists("chat_history.json"):
            with open("chat_history.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
    return []

def save_chat_history():
    """Save chat history to persistent storage"""
    try:
        with open("chat_history.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving chat history: {e}")

def clear_persistent_chat():
    """Clear persistent chat history"""
    try:
        if os.path.exists("chat_history.json"):
            os.remove("chat_history.json")
        st.session_state.chat_history = []
        st.session_state.ai_client.clear_conversation_history()
    except Exception as e:
        st.error(f"Error clearing chat history: {e}")

def get_cache_key(documents_hash, analysis_type, personality):
    """Generate a unique cache key for analysis results"""
    key_string = f"{documents_hash}_{analysis_type}_{personality}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_documents_hash():
    """Generate hash of current documents for cache key"""
    if "documents" not in st.session_state:
        return ""
    doc_content = ""
    for filename, doc_info in st.session_state.documents.items():
        if doc_info["success"]:
            doc_content += f"{filename}_{doc_info['word_count']}_"
    return hashlib.md5(doc_content.encode()).hexdigest()

def get_cached_analysis(analysis_type):
    """Get cached analysis if available"""
    try:
        if "cached_analyses" not in st.session_state or "ai_client" not in st.session_state:
            return None
        documents_hash = get_documents_hash()
        personality = st.session_state.ai_client.current_personality
        cache_key = get_cache_key(documents_hash, analysis_type, personality)
        cached_data = st.session_state.cached_analyses.get(cache_key)
        if cached_data:
            return cached_data
        return None
    except:
        return None

def save_analysis_cache(analysis_type, content):
    """Save analysis result to cache"""
    try:
        if "cached_analyses" not in st.session_state or "ai_client" not in st.session_state:
            return
        documents_hash = get_documents_hash()
        personality = st.session_state.ai_client.current_personality
        cache_key = get_cache_key(documents_hash, analysis_type, personality)
        cache_entry = {
            "content": content,
            "timestamp": time.time(),
            "personality": personality,
            "analysis_type": analysis_type
        }
        st.session_state.cached_analyses[cache_key] = cache_entry
    except Exception as e:
        st.error(f"Error saving analysis cache: {e}")

# FIXED: Regenerate button callback functions
def regenerate_summary():
    """Callback to regenerate summary"""
    clear_analysis_cache("summary")
    st.session_state.force_regenerate_summary = True

def regenerate_key_points():
    """Callback to regenerate key points"""
    clear_analysis_cache("key_points")
    st.session_state.force_regenerate_key_points = True

def regenerate_sentiment():
    """Callback to regenerate sentiment"""
    clear_analysis_cache("sentiment")
    st.session_state.force_regenerate_sentiment = True

def regenerate_mindmap():
    """Callback to regenerate mind map"""
    clear_analysis_cache("mind_map")
    st.session_state.force_regenerate_mindmap = True

def clear_analysis_cache(analysis_type):
    """Clear cache for specific analysis type"""
    try:
        documents_hash = get_documents_hash()
        personality = st.session_state.ai_client.current_personality
        cache_key = get_cache_key(documents_hash, analysis_type, personality)
        if cache_key in st.session_state.cached_analyses:
            del st.session_state.cached_analyses[cache_key]
    except Exception as e:
        st.error(f"Error clearing cache: {e}")

# FIXED: Interactive button callback functions
def explore_topic_callback(topic_data):
    """Callback for explore topic button"""
    st.session_state.pending_exploration = {
        "topic": topic_data,
        "action": "explore",
        "timestamp": time.time()
    }

def generate_details_callback(topic_data):
    """Callback for generate details button"""
    st.session_state.pending_details = {
        "topic": topic_data,
        "action": "details",
        "timestamp": time.time()
    }

def comprehensive_analysis_callback(theme_data):
    """Callback for comprehensive analysis button"""
    st.session_state.pending_analysis = {
        "topic": theme_data,
        "action": "analysis",
        "timestamp": time.time()
    }

def extract_data_points_callback(theme_data):
    """Callback for extract data points button"""
    st.session_state.pending_data_extraction = {
        "topic": theme_data,
        "action": "data_extraction",
        "timestamp": time.time()
    }

def discuss_theme_callback(theme_data):
    """Callback for discuss theme button"""
    st.session_state.pending_discussion = {
        "topic": theme_data,
        "action": "discussion",
        "timestamp": time.time()
    }

# FIXED: Action handlers
def handle_pending_actions():
    """Handle any pending actions set by button callbacks"""
    
    # Handle exploration
    if "pending_exploration" in st.session_state:
        action = st.session_state.pending_exploration
        del st.session_state.pending_exploration
        
        topic = action["topic"]
        question = f"Tell me more about '{topic['name']}'. {topic.get('summary', '')} What are the key insights and details I should know?"
        
        # Add to chat
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        st.session_state.chat_messages.append({"role": "user", "message": question})
        st.success(f"Started exploration of '{topic['name']}' - check the Chat tab!", icon="✓")
    
    # Handle details
    if "pending_details" in st.session_state:
        action = st.session_state.pending_details
        del st.session_state.pending_details
        perform_details_generation(action["topic"])
    
    # Handle analysis
    if "pending_analysis" in st.session_state:
        action = st.session_state.pending_analysis
        del st.session_state.pending_analysis
        perform_comprehensive_analysis(action["topic"])
    
    # Handle data extraction
    if "pending_data_extraction" in st.session_state:
        action = st.session_state.pending_data_extraction
        del st.session_state.pending_data_extraction
        perform_data_extraction(action["topic"])
    
    # Handle discussion
    if "pending_discussion" in st.session_state:
        action = st.session_state.pending_discussion
        del st.session_state.pending_discussion
        
        topic = action["topic"]
        question = f"Let's discuss '{topic['name']}' in detail. {topic.get('summary', '')} What are the key aspects and implications?"
        
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        st.session_state.chat_messages.append({"role": "user", "message": question})
        st.success(f"Started discussion about '{topic['name']}' - check the Chat tab!", icon="✓")

def perform_comprehensive_analysis(theme_data):
    """Perform comprehensive analysis and display results"""
    try:
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if not all_text:
            st.warning("No documents available for analysis")
            return
            
        combined_text = "\n\n".join(all_text)
        theme_name = theme_data["name"]
        
        with st.spinner(f"🔍 Analyzing '{theme_name}'..."):
            analysis_prompt = f"""Provide a comprehensive analysis of '{theme_name}' based on the document content.
            
            Include:
            1. Overview and background
            2. Key findings and insights
            3. Supporting evidence from documents
            4. Implications and significance
            5. Related concepts and connections
            
            Document content: {combined_text[:10000]}"""
            
            response = st.session_state.ai_client._make_api_request(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            if response["success"]:
                st.success(f"🔍 Comprehensive Analysis: {theme_name}")
                st.write(response["content"])
            else:
                st.error(f"Analysis failed: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"Error in comprehensive analysis: {str(e)}")

def perform_data_extraction(theme_data):
    """Extract data points and display results"""
    try:
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        combined_text = "\n\n".join(all_text)
        theme_name = theme_data["name"]
        
        with st.spinner(f"📊 Extracting data for '{theme_name}'..."):
            data_prompt = f"""Extract all specific data points, statistics, numbers, dates, names, and factual information related to '{theme_name}'.
            
            Format as organized bullet points:
            • **Data Point**: [Specific fact/number/date]
            • **Statistic**: [Another specific fact]
            
            Document content: {combined_text[:10000]}"""
            
            response = st.session_state.ai_client._make_api_request(
                messages=[{"role": "user", "content": data_prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            if response["success"]:
                st.success(f"Data Points: {theme_name}", icon="✓")
                st.write(response["content"])
            else:
                st.error(f"Data extraction failed: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"Error in data extraction: {str(e)}")

def perform_details_generation(sub_theme_data):
    """Generate detailed notes and display results"""
    try:
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        combined_text = "\n\n".join(all_text)
        topic_name = sub_theme_data["name"]
        
        with st.spinner(f"Generating details for '{topic_name}'..."):
            details_prompt = f"""Generate comprehensive, detailed notes about '{topic_name}' based on the document content.
            
            Include:
            1. Detailed explanation of the concept
            2. Specific examples from the documents
            3. Step-by-step processes if applicable
            4. Key relationships and dependencies
            5. Important considerations
            
            Format as clear, organized notes with headers and bullet points.
            
            Document content: {combined_text[:10000]}"""
            
            response = st.session_state.ai_client._make_api_request(
                messages=[{"role": "user", "content": details_prompt}],
                max_tokens=2000,
                temperature=0.5
            )
            
            if response["success"]:
                st.success(f"Detailed Notes: {topic_name}", icon="✓")
                st.write(response["content"])
            else:
                st.error(f"Details generation failed: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"Error in details generation: {str(e)}")

# Page configuration
st.set_page_config(
    page_title="AI Document Analyzer & Chat",
    page_icon="attached_assets/process_1756730569550.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "processor" not in st.session_state:
    st.session_state.processor = DocumentProcessor()
if "icons_loaded" not in st.session_state:
    load_png_icons()
    st.session_state.icons_loaded = True
if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()
if "ai_client" not in st.session_state:
    st.session_state.ai_client = AIClient()
if "mindmap_generator" not in st.session_state:
    st.session_state.mindmap_generator = MindMapGenerator(st.session_state.ai_client)
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()
if "current_document" not in st.session_state:
    st.session_state.current_document = None
if "cached_analyses" not in st.session_state:
    st.session_state.cached_analyses = load_cached_analyses()
if "mindmap_data" not in st.session_state:
    st.session_state.mindmap_data = None

def display_mind_map_results(mind_map_data):
    """Display mind map results in multiple formats"""
    if isinstance(mind_map_data, str):
        st.error("Mind map data is in text format, not structured data")
        st.text_area("Raw Response", mind_map_data, height=200)
        return
        
    if "error" in mind_map_data:
        st.error(f"Error in mind map data: {mind_map_data['error']}")
        return
    
    # Store in session state for potential reuse
    st.session_state.mindmap_data = mind_map_data
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Tree View", "Markdown", "Mermaid Diagram"])
    
    with tab1:
        st.write("**Interactive Mind Map Structure**")
        display_mind_map_tree(mind_map_data)
    
    with tab2:
        st.write("**Markdown Export**")
        markdown_content = st.session_state.mindmap_generator.export_to_markdown(mind_map_data)
        st.markdown(markdown_content)
        st.download_button(
            "📄 Download Markdown",
            markdown_content,
            "mindmap.md",
            "text/markdown"
        )
    
    with tab3:
        st.write("**Interactive Mermaid Diagram**")
        mermaid_content = st.session_state.mindmap_generator.export_to_mermaid(mind_map_data)
        
        if mermaid_content and len(mermaid_content.strip()) > 10:
            # Just show the diagram using simple HTML
            streamlit.components.v1.html(f"""
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
            <div class="mermaid">
            {mermaid_content}
            </div>
            <script>
            mermaid.initialize({{startOnLoad:true}});
            </script>
            """, height=500)
            
            # Show code for debugging
            with st.expander("View Mermaid Code"):
                st.code(mermaid_content, language="mermaid")
        else:
            st.error("No valid mermaid content generated")

def display_mind_map_tree(mind_map_data):
    """FIXED: Display mind map as an interactive tree structure with working buttons"""
    
    # CRITICAL: Add this line at the beginning to handle button callbacks
    handle_pending_actions()
    
    title = mind_map_data.get("title", "Mind Map")
    themes = mind_map_data.get("themes", [])
    
    st.markdown(f"### {title}")
    
    if not themes:
        st.warning("No themes found in the mind map")
        return
    
    for i, theme in enumerate(themes):
        with st.expander(f"{theme['name']}", expanded=False):
            # Theme summary with better formatting
            if theme.get('summary'):
                st.markdown(f"**Summary:** {theme['summary']}")
            else:
                st.markdown("**Summary:** No summary available")
            
            st.markdown("---")
            
            # FIXED: Theme-level action buttons with proper callbacks
            col1, col2, col3 = st.columns(3)
            with col1:
                st.button(
                    "Discuss", 
                    key=f"discuss_{theme['id']}_{i}",
                    help=f"Start a conversation about '{theme['name']}'",
                    on_click=discuss_theme_callback,
                    args=(theme,),
                    use_container_width=True
                )
            with col2:
                st.button(
                    "Analyze", 
                    key=f"analyze_{theme['id']}_{i}",
                    help=f"Generate comprehensive analysis of '{theme['name']}'",
                    on_click=comprehensive_analysis_callback,
                    args=(theme,),
                    use_container_width=True
                )
            with col3:
                st.button(
                    "Data", 
                    key=f"data_{theme['id']}_{i}",
                    help=f"Extract specific data and facts about '{theme['name']}'",
                    on_click=extract_data_points_callback,
                    args=(theme,),
                    use_container_width=True
                )
            
            # Display sub-themes with improved formatting
            sub_themes = theme.get("sub_themes", [])
            if sub_themes:
                st.markdown("### Sub-topics:")
                for j, sub_theme in enumerate(sub_themes):
                    with st.container():
                        # Create a nice card-like appearance for sub-themes
                        st.markdown(f"**• {sub_theme['name']}**")
                        if sub_theme.get('summary'):
                            st.markdown(f"  *{sub_theme['summary']}*")
                        else:
                            st.markdown("  *No summary available*")
                        
                        # FIXED: Sub-theme action buttons with unique keys and callbacks
                        col1, col2 = st.columns(2)
                        with col1:
                            st.button(
                                "Explore", 
                                key=f"explore_{theme['id']}_{j}_{i}",
                                help=f"Deep dive into '{sub_theme['name']}'",
                                on_click=explore_topic_callback,
                                args=(sub_theme,),
                                use_container_width=True
                            )
                        with col2:
                            st.button(
                                "Details", 
                                key=f"detail_{theme['id']}_{j}_{i}",
                                help=f"Generate detailed notes for '{sub_theme['name']}'",
                                on_click=generate_details_callback,
                                args=(sub_theme,),
                                use_container_width=True
                            )

def explore_topic_in_chat(topic_data):
    """Add a topic exploration question to the chat"""
    try:
        topic_name = topic_data['name']
        topic_summary = topic_data.get('summary', '')
        
        # Create a focused question
        question = f"Tell me more about '{topic_name}'. {topic_summary} What are the key insights and details I should know?"
        
        # Add to chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        st.session_state.chat_messages.append({"role": "user", "message": question})
        
        st.success(f"✅ Added exploration question about '{topic_name}' to chat!")
        
    except Exception as e:
        st.error(f"Error in topic exploration: {str(e)}")

def generate_detailed_notes(topic_data):
    """Generate detailed notes for a specific topic"""
    try:
        topic_name = topic_data['name']
        topic_summary = topic_data.get('summary', '')
        
        question = f"Generate comprehensive, detailed notes about '{topic_name}'. Include specific facts, data, methodologies, and analysis. Context: {topic_summary}"
        
        # Process with AI
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if all_text:
            combined_text = "\n\n".join(all_text)
            response = st.session_state.ai_client.chat_with_document(
                question, combined_text[:8000]
            )
            
            if response["success"]:
                st.success(f"Detailed Notes: {topic_name}", icon="✓")
                st.write(response["content"])
            else:
                st.error(f"Failed to generate notes: {response['error']}")
        else:
            st.warning("No documents available for analysis")
            
    except Exception as e:
        st.error(f"Error generating detailed notes: {str(e)}")

def generate_comprehensive_analysis(theme_data):
    """Generate comprehensive analysis for a theme"""
    try:
        theme_name = theme_data['name']
        theme_summary = theme_data.get('summary', '')
        
        question = f"Provide a comprehensive analysis of '{theme_name}'. Include: 1) Overview and context, 2) Key findings and insights, 3) Supporting evidence, 4) Implications and significance, 5) Related concepts. Context: {theme_summary}"
        
        # Process with AI
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if all_text:
            combined_text = "\n\n".join(all_text)
            response = st.session_state.ai_client.chat_with_document(
                question, combined_text[:8000]
            )
            
            if response["success"]:
                st.success(f"🔍 Comprehensive Analysis: {theme_name}")
                st.write(response["content"])
            else:
                st.error(f"Failed to generate analysis: {response['error']}")
        else:
            st.warning("No documents available for analysis")
            
    except Exception as e:
        st.error(f"Error in comprehensive analysis: {str(e)}")

def extract_data_points(theme_data):
    """Extract specific data points and facts for a theme"""
    try:
        theme_name = theme_data['name']
        theme_summary = theme_data.get('summary', '')
        
        question = f"Extract all specific data points, statistics, numbers, dates, names, and factual information related to '{theme_name}'. Present as organized bullet points. Context: {theme_summary}"
        
        # Process with AI
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if all_text:
            combined_text = "\n\n".join(all_text)
            response = st.session_state.ai_client.chat_with_document(
                question, combined_text[:8000]
            )
            
            if response["success"]:
                st.success(f"Data Points: {theme_name}", icon="✓")
                st.write(response["content"])
            else:
                st.error(f"Failed to extract data points: {response['error']}")
        else:
            st.warning("No documents available for analysis")
            
    except Exception as e:
        st.error(f"Error extracting data points: {str(e)}")

def remove_document(filename):
    """Remove a document from the collection"""
    try:
        if filename in st.session_state.documents:
            del st.session_state.documents[filename]
            # Clear vector store for the removed document
            st.session_state.vector_store.clear()
            # Rebuild vector store with remaining documents
            for fname, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    st.session_state.vector_store.add_document(doc_info)
            st.success(f"Removed {filename}")
        else:
            st.error(f"Document {filename} not found")
    except Exception as e:
        st.error(f"Error removing document: {str(e)}")

def upload_document():
    """Handle document upload"""
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=['pdf', 'docx', 'doc', 'txt'],
        help="Supported formats: PDF, Word documents (.docx, .doc), Plain text (.txt)"
    )
    
    if uploaded_file is not None:
        if uploaded_file.name not in st.session_state.documents:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                # Process the document
                doc_result = st.session_state.processor.process_document(
                    uploaded_file, uploaded_file.name
                )
                
                # Store in session state
                st.session_state.documents[uploaded_file.name] = doc_result
                
                # Add to vector store if successful
                if doc_result["success"]:
                    st.session_state.vector_store.add_document(doc_result)
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                    st.info(f"📄 {doc_result['word_count']} words, {doc_result['chunk_count']} chunks")
                else:
                    st.error(f"❌ Failed to process {uploaded_file.name}: {doc_result['error']}")
        else:
            st.warning(f"Document {uploaded_file.name} already uploaded")

def display_documents():
    """Display uploaded documents"""
    if st.session_state.documents:
        st.write("**Uploaded Documents:**")
        for filename, doc_info in st.session_state.documents.items():
            with st.expander(f"📄 {filename}"):
                if doc_info["success"]:
                    st.write(st.session_state.processor.get_document_summary(doc_info))
                    if st.button(f"Remove {filename}", key=f"remove_{filename}"):
                        remove_document(filename)
                else:
                    st.error(f"Error: {doc_info['error']}")
                    if st.button(f"Remove {filename}", key=f"remove_{filename}"):
                        remove_document(filename)
    else:
        st.info("No documents uploaded yet")

def generate_fresh_summary():
    """Generate fresh document summary"""
    try:
        with st.status("Generating document summary...", expanded=True) as status:
            all_text = []
            document_titles = []
            
            for filename, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    all_text.append(doc_info["text"])
                    document_titles.append(filename)
            
            if not all_text:
                st.warning("No valid documents to analyze")
                return
            
            combined_text = "\n\n=== DOCUMENT SEPARATOR ===\n\n".join(all_text)
            st.write(f"📊 Analyzing {len(document_titles)} document(s)...")
            
            # Generate summary using AI
            response = st.session_state.ai_client.analyze_document(
                combined_text[:15000],  # Increased limit for better analysis
                "summary"
            )
            
            if response["success"]:
                content = response["content"]
                status.update(label="✅ Summary generated!", state="complete")
                
                # Cache the result
                save_analysis_cache("summary", content)
                
                # Display with regenerate option
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.button("🔄 Regenerate", key="regen_summary_new", on_click=regenerate_summary)
                
                st.write(content)
            else:
                st.error(f"Error generating summary: {response['error']}")
                
    except Exception as e:
        st.error(f"Error in summary generation: {str(e)}")

def generate_fresh_key_points():
    """Generate fresh key points analysis"""
    try:
        with st.status("Extracting key points...", expanded=True) as status:
            all_text = []
            
            for filename, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    all_text.append(doc_info["text"])
            
            if not all_text:
                st.warning("No valid documents to analyze")
                return
            
            combined_text = "\n\n".join(all_text)
            st.write("Identifying key insights and conclusions...")
            
            response = st.session_state.ai_client.analyze_document(
                combined_text[:15000],
                "key_points"
            )
            
            if response["success"]:
                content = response["content"]
                status.update(label="✅ Key points extracted!", state="complete")
                
                save_analysis_cache("key_points", content)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.button("🔄 Regenerate", key="regen_key_points_new", on_click=regenerate_key_points)
                
                st.write(content)
            else:
                st.error(f"Error extracting key points: {response['error']}")
                
    except Exception as e:
        st.error(f"Error in key points extraction: {str(e)}")

def generate_fresh_sentiment():
    """Generate fresh sentiment analysis"""
    try:
        with st.status("📈 Analyzing sentiment and tone...", expanded=True) as status:
            all_text = []
            
            for filename, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    all_text.append(doc_info["text"])
            
            if not all_text:
                st.warning("No valid documents to analyze")
                return
            
            combined_text = "\n\n".join(all_text)
            st.write("🎭 Examining emotional tone and attitudes...")
            
            response = st.session_state.ai_client.analyze_document(
                combined_text[:15000],
                "sentiment"
            )
            
            if response["success"]:
                content = response["content"]
                status.update(label="✅ Sentiment analysis complete!", state="complete")
                
                save_analysis_cache("sentiment", content)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.button("🔄 Regenerate", key="regen_sentiment_new", on_click=regenerate_sentiment)
                
                st.write(content)
            else:
                st.error(f"Error analyzing sentiment: {response['error']}")
                
    except Exception as e:
        st.error(f"Error in sentiment analysis: {str(e)}")

def generate_fresh_mind_map():
    """Generate fresh mind map"""
    try:
        all_text = []
        document_titles = []
        
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
                document_titles.append(filename)
        
        if not all_text:
            st.warning("No valid documents to analyze")
            return
        
        combined_text = "\n\n".join(all_text)
        
        # Generate mind map
        mind_map_data = st.session_state.mindmap_generator.generate_mind_map(
            combined_text, document_titles
        )
        
        if mind_map_data and "error" not in mind_map_data:
            # Cache the result
            save_analysis_cache("mind_map", mind_map_data)
            
            # Display with regenerate option
            col1, col2 = st.columns([3, 1])
            with col2:
                st.button("🔄 Regenerate", key="regen_mindmap_new", on_click=regenerate_mindmap)
            
            display_mind_map_results(mind_map_data)
        else:
            st.error(f"Failed to generate mind map: {mind_map_data.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"Error in mind map generation: {str(e)}")

# FIXED: Main analysis functions with proper regenerate handling
def generate_document_summary():
    """Generate document summary with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_summary", False):
        st.session_state.force_regenerate_summary = False
        generate_fresh_summary()
        return
    
    # Check cache
    cached_result = get_cached_analysis("summary")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("📄 Using cached analysis")
        with col2:
            st.button("🔄 Regenerate", key="regen_summary", on_click=regenerate_summary)
        
        st.write(cached_result["content"])
        return
    
    generate_fresh_summary()

def extract_key_points():
    """Extract key points with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_key_points", False):
        st.session_state.force_regenerate_key_points = False
        generate_fresh_key_points()
        return
    
    # Check cache
    cached_result = get_cached_analysis("key_points")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🎯 Using cached analysis")
        with col2:
            st.button("🔄 Regenerate", key="regen_key_points", on_click=regenerate_key_points)
        
        st.write(cached_result["content"])
        return
    
    generate_fresh_key_points()

def analyze_sentiment():
    """Analyze sentiment with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_sentiment", False):
        st.session_state.force_regenerate_sentiment = False
        generate_fresh_sentiment()
        return
    
    # Check cache
    cached_result = get_cached_analysis("sentiment")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("📈 Using cached analysis")
        with col2:
            st.button("🔄 Regenerate", key="regen_sentiment", on_click=regenerate_sentiment)
        
        st.write(cached_result["content"])
        return
    
    generate_fresh_sentiment()

def generate_mind_map():
    """Generate mind map with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_mindmap", False):
        st.session_state.force_regenerate_mindmap = False
        generate_fresh_mind_map()
        return
    
    # Check cache
    cached_result = get_cached_analysis("mind_map")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🧠 Using cached mind map")
        with col2:
            st.button("🔄 Regenerate", key="regen_mindmap", on_click=regenerate_mindmap)
        
        display_mind_map_results(cached_result["content"])
        return
    
    generate_fresh_mind_map()

# Modern dark UI styling
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding: 1rem 2rem;
        max-width: 100%;
        background-color: #0e1117;
    }
    
    /* Hide default streamlit elements */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        background-color: #0e1117;
    }
    
    /* Column styling - removed all boxes */
    
    /* Header styling */
    .panel-header {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #404040;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Chat messages styling - removed container box */
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        margin-bottom: 1rem;
    }
    
    /* Analysis cards - removed boxes */
    .analysis-result {
        margin-bottom: 1rem;
        color: #e0e0e0;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-1px);
    }
    
    /* Text styling */
    .stMarkdown {
        color: #e0e0e0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    
    /* Remove white backgrounds */
    .stExpander {
        background-color: transparent !important;
    }
    
    .stExpander > div {
        background-color: #2a2a2a !important;
        border: 1px solid #404040 !important;
    }
</style>
""", unsafe_allow_html=True)

# App header with logo
col1, col2 = st.columns([1, 4])
with col1:
    if "process_icon_b64" in st.session_state:
        st.markdown(f"<img src='data:image/png;base64,{st.session_state.process_icon_b64}' width='48' height='48' style='margin-bottom: 1rem;'>", unsafe_allow_html=True)
with col2:
    st.markdown("# AI Document Analyzer & Chat")
    st.markdown("*Upload documents and chat with them using AI*")

st.markdown("---")

# Main three-column layout
sources_col, chat_col, studio_col = st.columns([1, 2, 2])

# SOURCES COLUMN (Left)
with sources_col:
    
    # Sources header
    st.markdown('<div class="panel-header"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg> Sources</div>', unsafe_allow_html=True)
    
    # Document upload
    upload_document()
    
    st.markdown("---")
    
    # Document list
    display_documents()
    
    st.markdown("---")
    
    # AI Settings
    st.markdown(f"**<img src='data:image/png;base64,{st.session_state.get('gear_icon_b64', '')}' width='16' height='16' style='vertical-align: middle; margin-right: 4px;'> Settings**", unsafe_allow_html=True)
    
    # Model selection
    available_models = st.session_state.ai_client.available_models
    if available_models:
        current_model_key = None
        for key, value in available_models.items():
            if value == st.session_state.ai_client.current_model:
                current_model_key = key
                break
        
        if current_model_key:
            model_options = list(available_models.keys())
            current_index = model_options.index(current_model_key)
            
            selected_model = st.selectbox(
                "AI Model",
                options=model_options,
                index=current_index,
                help="Choose the AI model"
            )
            
            if selected_model != current_model_key:
                if st.session_state.ai_client.set_model(selected_model):
                    st.success(f"Switched to {selected_model}")
                else:
                    st.error(f"Failed to switch to {selected_model}")
    
    # Personality selection
    personalities = st.session_state.ai_client.get_available_personalities()
    personality_options = list(personalities.keys())
    
    current_personality_index = personality_options.index(st.session_state.ai_client.current_personality)
    
    selected_personality = st.selectbox(
        "AI Personality",
        options=personality_options,
        format_func=lambda x: personalities[x]["name"],
        index=current_personality_index,
        help="Choose AI personality"
    )
    
    if selected_personality != st.session_state.ai_client.current_personality:
        if st.session_state.ai_client.set_personality(selected_personality):
            st.success(f"Switched to {personalities[selected_personality]['name']}")
            st.session_state.cached_analyses = {}
        else:
            st.error(f"Failed to switch personality")
    
    # Clear chat button
    if st.button("Clear Chat", use_container_width=True, help="Clear chat history"):
        clear_persistent_chat()
        st.success("Chat cleared!")
    


# CHAT COLUMN (Middle)
with chat_col:
    
    # Chat header
    st.markdown('<div class="panel-header"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> Chat</div>', unsafe_allow_html=True)
    
    # Initialize chat messages
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Chat messages container (scrollable)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if st.session_state.documents:
        # Display chat history
        for i, message in enumerate(st.session_state.chat_messages):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["message"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["message"])
        
    
        
        # Chat input at bottom
        user_question = st.chat_input("Ask a question about your documents...")
        
        if user_question:
            # Add user message to chat
            st.session_state.chat_messages.append({"role": "user", "message": user_question})
            
            # Get relevant context from documents
            with st.spinner("Thinking..."):
                # Use vector store to find relevant chunks
                results = st.session_state.vector_store.search(user_question)
                
                if results:
                    context = "\n\n".join([result["chunk"]["text"] for result in results[:3]])
                else:
                    # Fallback: use first chunk of each document
                    context_parts = []
                    for filename, doc_info in st.session_state.documents.items():
                        if doc_info["success"] and doc_info["chunks"]:
                            context_parts.append(doc_info["chunks"][0]["text"])
                    context = "\n\n".join(context_parts)
                
                # Get AI response
                response = st.session_state.ai_client.chat_with_document(
                    user_question,
                    context,
                    max_tokens=1000
                )
                
                # Add response to chat
                if response["success"]:
                    ai_message = response["content"]
                    st.session_state.chat_messages.append({"role": "assistant", "message": ai_message})
                    save_chat_history()
                    st.rerun()
                else:
                    error_message = f"Sorry, I encountered an error: {response['error']}"
                    st.session_state.chat_messages.append({"role": "assistant", "message": error_message})
                    st.rerun()
    else:
    
        st.info("Upload documents to start chatting!")
    


# STUDIO COLUMN (Right) 
with studio_col:
    
    # Studio header with refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="panel-header"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10,8 16,12 10,16 10,8"/></svg> Studio</div>', unsafe_allow_html=True)
    with col2:
        if st.button("↻ Refresh", help="Refresh all analyses", type="secondary"):
            st.session_state.cached_analyses = {}
            st.rerun()
    
    if st.session_state.documents:
        # Analysis buttons in a grid
        st.markdown("**Generate Analysis**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Summary", use_container_width=True):
                generate_document_summary()
                st.rerun()
            if st.button("Key Points", use_container_width=True):
                extract_key_points()
                st.rerun()
        with col2:
            mindmap_icon = f"<img src='data:image/png;base64,{st.session_state.get('mindmap_icon_b64', '')}' width='16' height='16' style='vertical-align: middle; margin-right: 4px;'>"
            if st.button(f"{mindmap_icon} Mind Map", use_container_width=True):
                generate_mind_map()
                st.rerun()
            if st.button("Sentiment", use_container_width=True):
                analyze_sentiment()
                st.rerun()
        
        st.markdown("---")
        
        # Display cached analyses
        if st.session_state.cached_analyses:
            st.markdown("**Analysis Results**")
            
            # Summary section
            summary_cache = get_cached_analysis("summary")
            if summary_cache:
                with st.expander("Document Summary", expanded=True):
                    st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
                    st.write(summary_cache["content"])
                
            
            # Key points section
            key_points_cache = get_cached_analysis("key_points")
            if key_points_cache:
                with st.expander("Key Points", expanded=True):
                    st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
                    st.write(key_points_cache["content"])
                
            
            # Sentiment section
            sentiment_cache = get_cached_analysis("sentiment")
            if sentiment_cache:
                with st.expander("Sentiment Analysis", expanded=True):
                    st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
                    st.write(sentiment_cache["content"])
                
            
            # Mind map section
            mindmap_cache = get_cached_analysis("mind_map")
            if mindmap_cache:
                with st.expander("Mind Map", expanded=True):
                    st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
                    display_mind_map_results(mindmap_cache["content"])
                
        
    else:
        st.info("Upload documents to start analyzing!")
        st.markdown("**Welcome to AI Document Analyzer!**")
        st.markdown("**What you can do:**")
        
        # Feature list with SVG icons
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 8px 0;">
            <span style="margin-right: 8px;">{get_svg_icon("search", 16)}</span>
            <strong>Analyze Documents:</strong> Extract summaries, key points, and insights
        </div>
        <div style="display: flex; align-items: center; margin: 8px 0;">
            <span style="margin-right: 8px;">{get_svg_icon("brain", 16)}</span>
            <strong>Generate Mind Maps:</strong> Visual representations of document content
        </div>
        <div style="display: flex; align-items: center; margin: 8px 0;">
            <span style="margin-right: 8px;">{get_svg_icon("chat", 16)}</span>
            <strong>Chat with Documents:</strong> Ask questions and get contextual answers
        </div>
        <div style="display: flex; align-items: center; margin: 8px 0;">
            <span style="margin-right: 8px;">{get_svg_icon("users", 16)}</span>
            <strong>Multiple AI Personalities:</strong> Specialized perspectives
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Supported formats**: PDF, Word documents, Plain text")
        st.markdown("Upload your documents using the Sources section to begin!")
    
