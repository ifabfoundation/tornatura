import React from "react";

import "./App.css";
import { authStore } from "./providers/auth-providers";
import { useAppDispatch, useAppSelector } from "./hooks";
import { getUserInfo } from "./features/users/utils";
import { userActions, userSelectors } from "./features/users/state/user-slice";
import { userMenuSelectors } from "./features/userMenu/state/userMenu-slice";
import { Navigate, Outlet, useNavigate } from "react-router-dom";
import TopBar from "./components/Topbar";
import UserMenu from "./components/UserMenu";
import SideBar, { MenuItemEntry } from "./components/Sidebar";
import MobileHeaderBar from "./components/MobileHeaderBar";
import { companiesActions } from "./features/companies/state/companies-slice";
import logo from "./assets/images/logo.png";
import { AccountTypeEnum, AgriField } from "@tornatura/coreapis";
import { feedbacksActions } from "./features/feedbacks/state/feedbacks-slice";
import { fieldsActions } from "./features/fields/state/fields-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "./features/detections/state/detections-slice";
import { SidebarActions } from "./features/sidebar/state/sidebar-slice";

function SvgAnimated() {
  const svgStroke = "url(#pulseGradient)";
  const strokeWidth = 1;
  return (
    <svg
      viewBox="0 0 1586 2061"
      version="1.1"
      xmlns="http://www.w3.org/2000/svg"
      xmlnsXlink="http://www.w3.org/1999/xlink"
      preserveAspectRatio="xMidYMid slice"
    >
      <title>bg</title>
      <defs>
        {/* Radial gradient definition */}
        <radialGradient id="pulseGradient" cx="50%" cy="50%" r="0%" fx="50%" fy="50%">
          <stop offset="0%" stopColor="black" />
          <stop offset="50%" stopColor="#333" />
          <stop offset="100%" stopColor="black" />
          <animate attributeName="r" values="0%;100%;0%" dur="4s" repeatCount="indefinite" />
        </radialGradient>
        <path d="M0,0 L1586,0 L1586,2060 L0,2060 L0,0 Z" id="path-1"></path>
      </defs>
      <g id="bg" stroke="none" fill="none" transform="translate(0, 0.3898)" xlinkHref="#path-1">
        <use fill="#000000" fillRule="evenodd" xlinkHref="#path-1"></use>
        <path
          d="M849.583038,817.058209 C838.933505,736.699647 1010.53072,678.791495 958.533371,566.940713 C940.419941,527.977163 955.609989,501.231995 965.948545,483.549164"
          id="Path-13"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1033.72362,625.628827 C1040.59809,545.721608 1249.26059,565.45071 1272.41748,447.998989 C1284.21916,388.140888 1313.56919,351.818343 1347.34502,330.398141"
          id="Path-13"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M600.679996,623.262786 C447.706029,650.778908 433.623715,495.912111 289.731477,495.912111 C193.803318,495.912111 93.2639844,467.776517 -11.8865254,411.505327"
          id="Path-20"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1413.61204,901.156726 C1520.85913,928.672848 1530.73197,773.806051 1631.61204,773.806051"
          id="Path-20-Copy-9"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1197.66469,312.167204 C1350.63866,339.683326 1379.73629,157.079563 1588,145.385986"
          id="Path-20-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M776.458524,910.659228 C753.47806,798.972816 691.900584,774.163396 544.988207,761.79831 C398.07583,749.433224 408.755697,663.621724 280.889249,573.662916 C195.64495,513.690377 107.16782,490.585877 15.4578565,504.349417 L-102.60717,529.642156"
          id="Path-22"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M591.398675,766.15477 C591.398675,662.904667 364.886901,630.294016 343.941089,503.448531"
          id="Path-29"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M884.075409,1155.22033 C1035.17514,989.668279 1219.3263,1062.12241 1358.14656,960.525402 C1496.96683,858.928393 1431.3426,693.202293 1555.8362,646.707433 L1650.89054,632.448531"
          id="Path-19-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M959.519963,842.407438 C1039.06929,728.128428 1028.07317,628.455203 1041.48638,546.232993 C1054.55706,466.110445 1090.80633,402.55902 1256.60533,358.211497 C1480.56723,298.306696 1615.46735,196.81285 1661.30568,53.7299581"
          id="Path-10"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M795.680867,1036.23256 C801.361734,1005.96327 851.551631,964.734891 851.551631,860.260465 C851.551631,620.094598 668.211743,556.908325 719.790171,341.973019 C732.911488,287.294459 730.74676,242.989097 713.295986,209.056933"
          id="Path-11"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M776.311933,607.681834 C755.618635,460.441369 887.782749,489.964748 844.538863,274.483658 C815.709606,130.829598 834.256092,17.1033946 900.17832,-66.694952"
          id="Path-12"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M402.281184,435.609442 C298.994181,328.652619 423.270602,274.853418 261.628956,125.943672 C153.867859,26.6705085 102.025696,-76.2372733 106.102467,-182.779673"
          id="Path-12-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M798.680867,1039.14764 C874.76605,1015.8128 894.781777,920.362146 941.4869,861.204418 C1011.54458,772.467827 1120.77144,829.939768 1224.90941,627.116174 C1294.33472,491.900445 1391.49191,407.988212 1516.38096,375.379477 C1599.64033,353.640319 1686.03469,304.733932 1775.56402,228.660315"
          id="Path-12-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M830.697432,727.562959 C800.299192,492.481254 1104.65359,540.127865 1030.00349,195.791346 C1008.99512,98.8865918 1038.29562,29.0571951 1117.90499,-13.6968437"
          id="Path-12-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M776.748429,744.616696 C738.115063,657.844735 642.44491,710.629235 579.131601,585.033226 C515.818292,459.437217 406.11136,403.013511 199.800074,423.343811 C62.2592178,436.897345 -25.2069127,400.481418 -62.5983168,314.09603"
          id="Path-13-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1182.11883,381.707457 C1174.24582,270.493441 1309.67099,205.925499 1354.60159,117.420991 C1399.5322,28.9164838 1341.14914,-78.5682178 1404.29351,-171.103703"
          id="Path-15"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M787.756996,1038.29875 C768.912154,1015.2023 750.416193,1008.83333 731.317455,1002.72101 C702.811177,993.59791 652.737976,968.681511 635.859283,937.418223 C603.023745,876.599123 582.201439,847.24388 524.163826,820.700146 C437.094729,780.878749 324.327428,787.609724 252.191826,710.253761 C204.101424,658.683119 143.814498,637.501009 85.8227253,646.707433 C47.1615433,652.845048 -4.11956731,645.818846 -68.0206065,625.628827"
          id="Path-15-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M269.734462,970.851744 C256.883876,819.53301 133.700823,742.829632 56.9695188,710.625743 C-35.5544308,671.793731 -158.116098,684.325557 -232.694088,604.350454"
          id="Path-15-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1036.68815,361.859966 C1190.16888,270.493441 1042.14238,115.96226 1179.59697,-20.3668652"
          id="Path-16"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M823.305682,460.330653 C915.102914,432.046825 957.263163,369.151495 957.263163,304.948532 C957.263163,240.74557 919.598732,93.8175607 1015.12379,-6.82121026e-13"
          id="Path-17"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M654.176448,961.46031 C588.867885,967.634894 534.195329,967.634894 492.709833,945.636812 C444.284515,919.958824 352.733545,840.35401 233.098423,855.688709"
          id="Path-17-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M203.264234,933.658994 C151.542279,973.141196 99.28235,971.314801 62.6103825,945.636812 C25.9384149,919.958824 -43.3921406,840.35401 -133.99052,855.688709"
          id="Path-17-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M722.253006,484.808819 C784.18907,387.955404 756.222645,248.574196 676.74934,156.27204 C629.921858,101.885507 592.907973,-20.3668652 630.475259,-66.694952"
          id="Path-18"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M499.149234,484.808819 C527.309759,400.681261 392.396706,344.295844 392.396706,224.142929 C392.396706,103.990014 523.190276,54.3309393 488.496509,-105.556477"
          id="Path-19"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M170.617982,902.252672 C82.2032893,807.85243 -23.474848,864.765705 -104.006031,761.690491"
          id="Path-20-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1225.1581,265.998065 C1134.80405,129.014127 1310.65681,67.7645777 1255.95155,-69.0850727"
          id="Path-20-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M790.451494,1036.23256 C773.669417,970.90555 773.217923,886.535628 782.457311,818.856883 C804.636551,656.393388 605.950395,590.437937 633.014654,427.668689 C660.078912,264.89944 524.163826,230.157213 524.163826,129.954018 C524.163826,88.4226852 529.701207,59.0755629 540.775969,41.9126512"
          id="Path-14"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M631.246234,447.998989 C541.735994,400.922637 506.623842,351.537122 488.850527,240.74557 C471.077213,129.954018 519.569642,75.5375699 543.740133,36.6296819 C569.612328,-5.01748488 580.657455,-49.6807055 576.875512,-97.35998"
          id="Path-21"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1272.41748,218.100919 C1398.56512,203.416152 1422.90342,173.24579 1433.87561,101.933424 C1441.1904,54.391847 1490.5883,20.4481832 1582.06929,0.102432897"
          id="Path-22-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M706.764717,195.608271 C735.8827,112.542768 650.218383,-2.55332156 731.248282,-93.8175607"
          id="Path-23"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M406.318759,157.079563 C429.571455,72.185235 336.087114,-36.6548453 410.553358,-133.349129"
          id="Path-23-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M830.55034,145.385986 C792.268117,66.6732952 843.83563,-84.8061926 756.028317,-172.779673"
          id="Path-24"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M449.566259,1004.2402 C357.094832,1074.58138 317.518863,946.41509 188.073991,1060.90429 C101.77741,1137.23043 14.677806,1160.79469 -73.2248204,1131.59707"
          id="Path-12"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M105.110465,1118.87601 C68.0340994,1180.7325 -60.1757499,1188.18311 -81.1751257,1297.43128"
          id="Path-24"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M315.074252,184.81653 C276.792029,106.103839 328.359542,-45.3756488 240.552229,-133.349129"
          id="Path-24-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M203.133646,423.965691 C91.8845809,394.411918 102.513948,202.509139 -102.60717,218.017752"
          id="Path-24-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M435.304771,792.512343 C323.291197,761.686215 332.449299,567.334839 126.473727,581.421401 C-10.8433217,590.812442 -110.07448,536.272742 -171.219749,417.802302"
          id="Path-24-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M983.717669,1071.20333 C983.717669,939.999403 1184.63713,944.502591 1241.07313,861.55781 C1297.50913,778.61303 1238.5963,678.323838 1378.80464,564.940713 C1472.27686,489.351964 1562.97216,461.743774 1650.89054,482.116144"
          id="Path-25"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M799.215384,1042.44795 C868.290949,1042.44795 926.346829,1016.37606 973.383023,964.232289 C1014.09632,919.098011 1007.64055,888.250981 1095.35596,846.427681 C1175.91649,808.015878 1239.49609,757.148727 1286.09477,693.826228"
          id="Path-26"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1187.28138,907.213273 C1394.06825,937.061874 1350.37251,710.944988 1497.04721,692.007427"
          id="Path-27"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1286.09477,534.598845 C1368.51431,558.544302 1555.24628,401.078046 1661.30568,383.590359"
          id="Path-28"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M549.941089,1064.0451 C426.920276,956.186288 351.071631,1019.88193 245.983524,961.630638 C140.895417,903.379349 99.8294726,785.259021 16.3439988,761.448531 C-67.141475,737.63804 -106.638793,780.520846 -186.402922,749.549654"
          id="Path-19-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M354.236428,310.692178 C243.21413,301.551188 194.594084,183.560984 112.033523,135.078771 C29.4729613,86.5965574 -83.5700976,118.630262 -168.062035,54.9267301"
          id="Path-15"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M244.521787,259.94612 C98.649963,313.607861 57.8892534,163.539207 -83.8169379,188.525832"
          id="Path-20-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M128.121535,76.2751812 C140.600102,16.9893385 132.456923,-14.6984794 96.4464371,-55.7480572"
          id="Path-21-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M202.436833,215.240923 C202.165013,111.660616 175.041457,87.8717555 105.664291,69.1154461 C59.412847,56.6112398 31.3874945,12.1266946 21.5882335,-64.3381897"
          id="Path-22-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M733.061465,1268.57633 C743.710998,1348.93489 571.339217,1403.65054 623.336566,1515.50132 C641.449996,1554.46487 626.259948,1581.21004 615.921392,1598.89287"
          id="Path-13-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M549.146319,1454.81321 C542.271851,1534.72042 333.609346,1514.99132 310.452458,1632.44304 C298.650781,1692.30114 269.300745,1728.62369 235.524912,1750.04389"
          id="Path-13-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M982.189941,1457.17925 C1135.16391,1429.66312 1149.24622,1584.52992 1293.13846,1584.52992 C1437.0307,1584.52992 1606.71747,1644.49668 1686.76046,1750.04389"
          id="Path-20-Copy-8"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M385.205246,1768.27483 C232.231279,1740.75871 218.148965,1895.6255 74.256727,1895.6255"
          id="Path-20-Copy-7"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M806.995074,1176.00934 C829.971425,1286.60062 890.969353,1308.96207 1037.88173,1321.20591 C1184.79411,1333.44975 1174.11424,1418.41983 1301.98069,1507.49655 C1387.22499,1566.88103 1475.70212,1589.75898 1567.41208,1576.1304 L1685.47711,1551.08567"
          id="Path-22-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M992.928848,1318.9935 C992.928848,1422.2436 1217.98304,1450.14802 1238.92885,1576.9935"
          id="Path-29-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M786.117451,1041.57149 C761.200972,1038.27117 722.019009,1048.31646 698.537603,1054.52887 C562.292629,1090.57484 388.806516,1016.02638 224.723372,1119.91663 C33.1744934,1241.19697 150.660026,1401.49864 26.1664227,1447.9935 C-56.829313,1478.99008 -115.579666,1487.24564 -150.084638,1472.7602"
          id="Path-19-Copy-5"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M623.349974,1238.03459 C543.800646,1352.3136 554.796763,1451.98683 541.383557,1534.20904 C528.312876,1614.33159 492.063609,1677.88301 326.264612,1722.23054 C102.302705,1782.13534 -32.5974139,1883.62918 -78.4357451,2026.71207"
          id="Path-10-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M754.008885,1110.20974 C738.83515,1140.2168 731.27141,1176.87407 731.317455,1220.18157 C731.574678,1458.01699 914.658195,1523.53371 863.079766,1738.46901 C849.958449,1793.14757 852.123177,1837.45294 869.573951,1871.3851"
          id="Path-11-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M806.558004,1472.7602 C827.251302,1620.00066 695.087188,1590.47728 738.331074,1805.95837 C767.160331,1949.61243 748.613845,2063.33864 682.691617,2147.13698"
          id="Path-12-Copy-7"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1180.58875,1644.83259 C1283.87576,1751.78941 1159.59934,1805.58861 1321.24098,1954.49836 C1429.00208,2053.77152 1480.84424,2156.67931 1476.76747,2263.22171"
          id="Path-12-Copy-6"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M790,1048.66333 C768.035726,1121.82706 688.08816,1160.07989 641.383037,1219.23761 C571.325353,1307.97421 462.098498,1250.50226 357.960529,1453.32586 C288.535217,1588.54159 191.378032,1672.45382 66.4889742,1705.06256 C-16.7703977,1726.80171 -103.164752,1775.7081 -192.694088,1851.78172"
          id="Path-12-Copy-5"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M751.86434,1355.39107 C782.26258,1590.47277 478.216351,1540.31417 552.866447,1884.65069 C573.874817,1981.55544 544.574316,2051.38484 464.964942,2094.13888"
          id="Path-12-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M806.121508,1335.82534 C844.754874,1422.5973 940.425028,1369.8128 1003.73834,1495.40881 C1067.05165,1621.00481 1176.75858,1677.42852 1383.06986,1657.09822 C1520.61072,1643.54469 1608.07685,1679.96061 1645.46825,1766.346"
          id="Path-13-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M400.751104,1698.73457 C408.624116,1809.94859 273.198952,1874.51653 228.268347,1963.02104 C183.337741,2051.52555 241.720801,2159.01025 178.576424,2251.54574"
          id="Path-15-Copy-6"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M798.215384,1046.66333 C821.911035,1064.27592 842.027431,1095.38356 851.344281,1111.76216 C901.151223,1199.3205 997.877199,1231.92154 1058.70611,1259.74189 C1145.77521,1299.56328 1258.54251,1292.83231 1330.67811,1370.18827 C1378.76851,1421.75891 1431.8096,1442.94102 1489.80137,1433.7346 C1528.46256,1427.59698 1585.63066,1427.59698 1661.30568,1433.7346"
          id="Path-15-Copy-5"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1228.41588,1120.18475 C1277.49207,1263.89984 1415.57228,1308.52412 1497.81516,1321.20843 C1596.98507,1336.5034 1712.87441,1294.69347 1804.58484,1354.25092"
          id="Path-15-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1301.9094,1140.19212 C1342.54338,1089.37003 1393.69281,1078.49935 1435.48754,1094.54284 C1477.28226,1110.58634 1563.81155,1171.05397 1648.00897,1134.25704"
          id="Path-17-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1341.1838,1162.76769 C1449.80968,1232.9744 1538.58016,1152.18583 1641.65537,1232.71702"
          id="Path-20-Copy-6"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M910.354473,1130.87888 C1055.81445,1205.77239 1137.6333,1092.28822 1253.6921,1123.38608 C1369.75091,1154.48395 1438.17291,1259.16084 1524.93879,1262.0671 C1611.70467,1264.97335 1639.65445,1213.80908 1724.54186,1224.56361"
          id="Path-19-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M546.181792,1718.58207 C392.701062,1809.94859 540.727559,1964.47977 403.272969,2100.8089"
          id="Path-16-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M759.564255,1620.11138 C667.767023,1648.39521 625.606774,1711.29054 625.606774,1775.4935 C625.606774,1839.69646 663.271205,1986.62447 567.746144,2080.44203"
          id="Path-17-Copy-5"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1342.16429,971.297874 C1393.88625,931.815672 1453.48759,945.619886 1490.15955,971.297874 C1526.83152,996.975862 1596.16208,1076.58068 1686.76046,1061.24598"
          id="Path-17-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M860.616931,1595.63321 C798.680867,1692.48663 826.647292,1831.86784 906.120597,1924.16999 C952.94808,1978.55652 989.961964,2100.8089 952.394678,2147.13698"
          id="Path-18-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1083.7207,1595.63321 C1055.56018,1679.76077 1190.47323,1736.14619 1190.47323,1856.2991 C1190.47323,1976.45202 1059.67966,2026.11109 1094.37343,2185.99851"
          id="Path-19-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M357.711837,1814.44397 C448.065886,1951.42791 272.213127,2012.67745 326.91839,2149.5271"
          id="Path-20-Copy-5"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M795.298536,1048.66333 C811.274629,1102.78008 809.662054,1193.83286 800.412626,1261.58515 C778.233386,1424.04864 976.919542,1490.00409 949.855283,1652.77334 C922.791025,1815.54259 1058.70611,1850.28482 1058.70611,1950.48801 C1058.70611,1992.01935 1053.16873,2021.36647 1042.09397,2038.52938"
          id="Path-14-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M951.623703,1632.44304 C1041.13394,1679.5194 1076.2461,1728.90491 1094.01941,1839.69646 C1111.79272,1950.48801 1063.3003,2004.90446 1039.1298,2043.81235 C1013.25761,2085.45952 1002.21248,2130.12274 1005.99442,2177.80201"
          id="Path-21-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M310.452458,1862.34111 C184.304814,1877.02588 159.966521,1907.19624 148.99433,1978.50861 C141.679536,2026.05019 92.2816405,2059.99385 0.800643776,2080.3396"
          id="Path-22-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M876.10522,1884.83376 C846.987237,1967.89926 932.651555,2082.99535 851.621655,2174.25959"
          id="Path-23-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1176.55118,1923.36247 C1153.29848,2008.2568 1246.78282,2117.09688 1172.31658,2213.79116"
          id="Path-23-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M752.319597,1935.05605 C790.60182,2013.76874 739.034307,2165.24822 826.84162,2253.22171"
          id="Path-24-Copy-7"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1267.79569,1895.6255 C1306.07791,1974.33819 1254.5104,2125.81768 1342.31771,2213.79116"
          id="Path-24-Copy-6"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1379.73629,1656.47634 C1490.98536,1686.03011 1480.35599,1877.93289 1685.47711,1862.42428"
          id="Path-24-Copy-5"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1147.56517,1287.92969 C1259.57874,1318.75582 1250.42064,1513.10719 1456.39621,1499.02063 C1593.71326,1489.62959 1692.94442,1544.16929 1754.08969,1662.63973"
          id="Path-24-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M588.867885,1067.02364 C583.084648,1073.70168 570.890897,1084.09439 552.286633,1098.20176 C489.347341,1145.92781 380.896534,1161.4188 341.796804,1218.88422 C285.360805,1301.829 344.273632,1402.11819 204.065301,1515.50132 C110.59308,1591.09007 19.8977827,1618.69826 -68.0205911,1598.32589"
          id="Path-25-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M571.901914,1083.55751 C571.901914,1148.4005 527.215712,1205.62529 437.843308,1255.23189 C378.261705,1288.30296 331.238992,1332.0976 296.775167,1386.6158"
          id="Path-26-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M395.588561,1173.22876 C188.801688,1143.38016 232.497428,1369.49704 85.8227253,1388.43461"
          id="Path-27-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M296.775167,1545.84319 C214.355626,1521.89773 27.6236604,1679.36399 -78.4357451,1696.85167"
          id="Path-28-Copy"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1228.63351,1769.74985 C1339.65581,1778.89084 1388.27585,1896.88105 1470.83641,1945.36326 C1553.39698,1993.84547 1666.44003,1961.81177 1750.93197,2025.5153"
          id="Path-15-Copy-3"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1338.34815,1820.49591 C1484.21997,1766.83417 1524.98068,1916.90283 1666.68687,1891.9162"
          id="Path-20-Copy-4"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1454.7484,2004.16685 C1442.26983,2063.45269 1450.41301,2095.14051 1486.4235,2136.19009"
          id="Path-21-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
        <path
          d="M1380.4331,1865.20111 C1380.70492,1968.78142 1407.82848,1992.57028 1477.20565,2011.32659 C1523.45709,2023.83079 1551.48244,2068.31534 1561.2817,2144.78022"
          id="Path-22-Copy-2"
          stroke={svgStroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        ></path>
      </g>
    </svg>
  );
}

export function Loading() {
  return (
    <>
      <div className="loading-cont">
        <div className="bg">
          <SvgAnimated />
        </div>
        <div className="icon">
          <img className="blink" src={logo} alt="loading" width="50px" />
          <p className="color-white mt-2"></p>
        </div>
      </div>
    </>
  );
}

export function RouteApp() {
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  if (currentUser.accountType === AccountTypeEnum.Admin) {
    return <Navigate to="/admin/companies" />;
  } else if (currentUser.accountType === AccountTypeEnum.Agronomist) {
    return <Navigate to="/companies" />;
  } else {
    // @ts-ignore
    // const url = `/companies/${currentUser.organizations[0].id}`;
    // return <Navigate to={url} />;
    return <Navigate to="/companies" />;
  }
}

function MainApp() {
  const userMenuOpen = useAppSelector(userMenuSelectors.selectIsOpen);
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);

  React.useEffect(() => {
    if (currentUser) {
      let menuEntries: MenuItemEntry[] = [];
      let menuBottomEntries: MenuItemEntry[] = [];

      if (currentUser.accountType === AccountTypeEnum.Admin) {
        menuEntries = [
          {
            id: "companies",
            icon: "grid",
            text: "Aziende",
            path: "/admin/companies",
          },
          {
            id: "users",
            icon: "users",
            text: "Utenti",
            path: "/admin/users",
          },
          {
            id: "feedbacks",
            icon: "baloon",
            text: "Feedbacks",
            path: "/admin/feedbacks",
          },
        ];

        menuBottomEntries = [
          {
            id: "user",
            icon: "users",
            text: "Profilo Utente",
            path: "/profile",
          },
        ];
        dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
        dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
      }
    }
  }, [currentUser]);

  return (
    <div id="app" className="main-app">
      <SideBar />
      <MobileHeaderBar />
      <UserMenu open={userMenuOpen} />
      <div className="ui-right">
        <TopBar /* showBackButton */ />
        <div className="content-area">
          <div className="content">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const navigate = useNavigate();
  const { initialized, authenticated } = React.useContext(authStore);
  const [loaded, setLoaded] = React.useState(false);
  const dispatch = useAppDispatch();

  const loadData = async () => {
    const profile = await getUserInfo();
    if (profile) {
      await dispatch(userActions.setCurrentUserAction(profile));

      const session = sessionStorage.getItem("pending_invitation_token");
      let invitationToken = undefined;
      if (session) {
        const invitation = JSON.parse(session);
        if (invitation.has_pending_invitation) {
          invitationToken = invitation.pending_invitation_token;
        }
        sessionStorage.removeItem("pending_invitation_token");
      }

      if (invitationToken) {
        // const redirectUri = `${window.location.origin}/invitations/accept?token=${invitationToken}`;
        navigate(`/invitations/accept?token=${invitationToken}`);
      }

      if (profile.accountType === AccountTypeEnum.Admin) {
        await dispatch(userActions.fetchUsersAction());
        await dispatch(companiesActions.fetchCompaniesAction());
        await dispatch(feedbacksActions.fetchFeedbackAction());
      } else if (
        profile.accountType === AccountTypeEnum.Agronomist ||
        profile.accountType === AccountTypeEnum.Standard
      ) {
        if (profile.organizations) {
          for (let org of profile.organizations) {
            await dispatch(companiesActions.getCompanyAction(org.id));
            const response = await dispatch(fieldsActions.fetchCompanyFieldsAction(org.id));
            const responseData = await unwrapResult(response);
            const fields = responseData.data as AgriField[];
            for (let field of fields) {
              await dispatch(
                detectionsActions.fetchFieldDetectionsAction({
                  orgId: org.id,
                  fieldId: field.id,
                })
              );
            }
          }
        }
      }
      setLoaded(true);
    }
  };

  React.useEffect(() => {
    if (initialized && authenticated) {
      loadData();
    }
  }, [authenticated, initialized]);

  // return <Loading />;

  if (!initialized) {
    return <Loading />;
  } else if (!authenticated) {
    return <Navigate to="/welcome" />;
  } else if (!loaded) {
    return <Loading />;
  } else {
    return <MainApp />;
  }
}

export default App;
