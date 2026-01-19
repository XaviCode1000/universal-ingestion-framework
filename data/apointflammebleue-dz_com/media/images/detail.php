
<html>
<head>
	<meta charset="utf-8">
	<link rel="icon" type="image/png" href="img/login/LOGO.png" />
	<script src="https://code.jquery.com/jquery-latest.min.js" type="text/javascript"></script>
	<link href="https://fonts.googleapis.com/css?family=Roboto:400,700" rel="stylesheet">
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"/>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<link rel="stylesheet" href="css/mycss1.css"/>
	


</head>
<body id="body1" onscroll="f_scroll()"> 
  	
<style type="text/css">
		html { scroll-behavior: smooth;}
		body{
			text-align:left;color:gray;
			font-family:'Roboto' , Arial;
			font-weight:400;width:100%;
			height:100%;
			margin:0px;
			padding:0px;
			overflow-x: hidden;
		}
		a{text-decoration:none;color: black}
		a:hover{color:#697fbd;}

/* ================================== MENU =========================*/
/* ================================== MENU =========================*/
/* ================================== MENU =========================*/
.fixed{
	xposition: fixed;
	top: 0px;
	left: 0px;
	width: 100%;
	z-index: 3;
}
#menu_container{
	display: flex;
  	justify-content: space-between;
  	padding: 20px 0px 10px 20px;
  	background: white;
  	flex-wrap: wrap !important;
  	overflow: hidden;
  	align-items: flex-start;
}
/* ================================== LOGO =========================*/
#menu_container img{
	width: 70px;
	display: block;
}

/* ================================== LIENS =========================*/
#menu_container nav{
	text-align: right;
	font-size: 1.4vw;
}

/* ================================== AR EN =========================*/
#menu_container nav div{
	display: inline-block;
	width: 19.5%;
	text-align: center;
	padding-top: 5px;
}

#ar{
	padding: 0px 5px;
	border-left:  2px solid #697fbd;
	border-right: 2px solid #697fbd;
	color: gray;
}
#en{
	padding: 0px 5px;
	border-right: 2px solid #697fbd;
	color: gray;
}


/* ================================== Les liens =========================*/

#menu_container nav ul{
	list-style: none;
	padding: 0px;
	margin: 0px;
}

#menu_container nav ul li{
	display: inline-block;
	vertical-align: top;
	text-align: center;
	padding: 5px 0px;
	border-top: 1px solid gray;
	border-bottom: 1px solid gray;
	margin-right:-5px ;	

}

#menu_container nav ul li a{
	padding: 0px 10px;
	border-right: 2px solid #697fbd;
	color: gray;
}

#pro{
	background: #697fbd;
	border-top: 1px solid #697fbd !important;
	border-bottom: 1px solid #697fbd !important;
	margin-right:0px ;	
	
}

#pro a{
	color: white !important;
	padding:  0px 20px !important;
}

.recrutement{
	border: none !important;
}

.mobile{
	display: none !important;
}


/* ================================== Responsive Mobile =========================*/

@media(max-width: 800px){
	.mobile{
		display: inline-block !important;
	}
	.pc{
		display: none !important;
	}
	#menu_container{
		  	align-items: flex-end;
	}
	#menu_container img{
	width: 45px;
	}

	#menu_container nav{
	font-size: 8px;
	}

	#menu_container nav ul li a{
	padding: 0px 7px;
	border-right: 1px solid #697fbd;	
	}
}



/* ================================== Open close menu =========================*/

.global_container{
	width: 100%;
}

.website_side_menu{
	position: fixed;width:200px;height:100%;background-color: white;left: 0px;
}

.content_container{
	position: absolute;top:0px;left:200px;width:100%;overflow-x: hidden;background: white;
}


.website_side_menu-active{
	position: fixed;width:200px;height:100%;background-color: white;left: -200px;
}

.content_container-active{
	position: absolute;top:0px;left:0px;width:100%;overflow-x: hidden;background: white;
}

.animx1{-webkit-transition: all 0.5s ;-moz-transition: all 0.5s ;-o-transition: all 0.5s ;-ms-transition: all 0.5s ;transition: all 0.5s ;}
/* ================================== Side menu =========================*/
#website_side_menu{
	background: #f8f8f8;
box-shadow: 3px 2px 41px -19px rgba(0,0,0,0.56) inset;
-webkit-box-shadow: 3px 2px 41px -19px rgba(0,0,0,0.56) inset;
-moz-box-shadow: 3px 2px 41px -19px rgba(0,0,0,0.56) inset;
}
#website_side_menu ul{
	list-style: none;
	padding: 0px;
	margin: 0px;
}

#website_side_menu ul li{
	padding: 10px 0px 10px 20px;
	border-bottom: 1px solid #dfdfdf;


box-shadow: -9px -14px 3px -11px rgba(255,255,255,0.4) inset;
-webkit-box-shadow: -9px -14px 3px -11px rgba(255,255,255,0.4) inset;
-moz-box-shadow: -9px -14px 3px -11px rgba(255,255,255,0.4) inset;



}

#website_side_menu ul li a{
	color: gray;
}

.active, a.active a.hover {
    color :#697fbd;
}
</style>

<!-- ====================Fonction Couleur Hover & active sur le menu ===============================-->
<script type="text/javascript">
 $(function($) {
 let url = window.location.href;
  $('#website_side_menu ul li a').each(function() {
   if (this.href === url) {
   $(this).addClass('active');
  }
 });
});
</script>

<!-- ====================================================== MENU =================================== -->
<!-- ====================================================== MENU =================================== -->
<!-- ====================================================== MENU =================================== -->
<!-- ====================================================== MENU =================================== -->
<div class="global_container">
	<div id="website_side_menu" class="website_side_menu-active">
		<ul>
				<li>
					<a href="index.php">ACCUEIL</a>
				</li>
				<li>
					<a href="notre_marque.php">NOTRE MARQUE</a>
				</li>
				<li>
					<a href="nos_produits.php">NOS PRODUITS</a>
				</li>
				<li>
					<a href="sav.php">SAV</a>
				</li>
				<li>
					<a href="Doc/CATALOGUE PRODUIT.pdf" target="_blank">CATALOGUE</a>
				</li>
				<li>
				    <a class='recrutement' href='recrutement.php'>RECRUTEMENT</a>					<!--<a class="recrutement" href="recrutement.php">RECRUTEMENT</a>-->
				</li>
				<li>
					<a class="recrutement" href="pre_contact.php">CONTACT</a>
				</li>
				<li style="background: #697fbd;">
					<a href="pro_login.php" style="color:white">PROFESSIONNEL</a>
				</li>
				<li>
					<a href="#" target="_blank">EN</a>
				</li>
				
				<li>
					<a  class="recrutement" href="#">AR</a>
				</li>
				
		</ul>


	</div>
	
	<!-- ====================Fonction Couleur Hover & active sur le menu ===============================-->
<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js">
 $(function($) {
 let url = window.location.href;
  $('#menu_link_container nav ul li a').each(function() {
   if (this.href === url) {
   $(this).addClass('active');
  }
 });
});
</script>
	<div id="content_container" class="content_container-active">
<div class="fixed">
	<div id="menu_container">
		<a href="index.php" style="color:#697fbd;"><img src="img/LOGO_APOINT.png"></a>
		<nav id="menu_link_container">
			<ul>
				<li class="mobile" onclick="side_menu()">
					<a href="#" style="color:#697fbd;">MENU</a>
				</li>
				<li>
					<a href="index.php" >ACCUEIL</a>
				</li>
				<li>
					<a href="notre_marque.php">NOTRE MARQUE</a>
				</li>
				<li class="pc">
					<a href="nos_produits.php">NOS PRODUITS</a>
				</li>
				<li class="pc">
					<a href="sav.php">SAV</a>
				</li>
				<li class="pc">
					<a href="Doc/CATALOGUE PRODUIT.pdf" target="_blank">CATALOGUE</a>
				</li>
				<li class="pc">
					<a href='recrutement.php'>RECRUTEMENT</a>				</li>
				<li class="pc">
					<a class="recrutement" href="pre_contact.php">CONTACT</a>
				</li>
				<li class="mobile">
					<a href="#" target="_blank">EN</a>
				</li>
				
				<li class="mobile">
					<a  class="recrutement" href="#">AR</a>
				</li>
				<li id="pro">
					<a href="pro_login.php" >PROFESSIONNEL</a>
				</li>
			</ul>
			<div class="pc"><a id="ar" href="#">AR</a><a id="en" href="#">EN</a></div>
		</nav>
	</div>
</div>


<script type="text/javascript">
	stete_side_menu=0;
	function side_menu(){
		if(stete_side_menu==0){ // =======> ouvrir
			$("#website_side_menu").removeClass("website_side_menu-active").addClass("website_side_menu").addClass("animx1");
			$("#content_container").removeClass("content_container-active").addClass("content_container").addClass("animx1");
			stete_side_menu=1;
		}else{ // =======> fermer
			$("#website_side_menu").removeClass("website_side_menu").addClass("website_side_menu-active").addClass("animx1");
			$("#content_container").removeClass("content_container").addClass("content_container-active").addClass("animx1");
			stete_side_menu=0;
		}
	}

</script>
<!-- ====================================================== MENU =================================== -->
<!-- ====================================================== MENU =================================== -->
<!-- ====================================================== MENU =================================== -->
<!-- ====================================================== MENU =================================== -->
<div style="position:fixed;bottom:5%;left:2%;z-index:5;width:4%;min-width:40px"><a href="javascript:history.go(-1)"><img src="img/icon/retour2.png" width="100%"></a></div>

<!-- =================================  mise à jour du produit ========================= -->
	<!-- =================================  /mise à jour du produit ========================= -->

<!-- =================================  compteur du nombre de visite mensuel ========================= -->
	<!-- =================================  /mise à jour du produit ========================= -->




<!-- =================================== / header : logo + 2 icones ============================== -->	

	




<style>
.button_container{
	color:white;
	background: #cc0628;
	position: absolute;
	top: 25px;
	left: 0px;
	padding:10px;
	text-align: center;
	border-radius: 0px 10px 10px 0px; 
	cursor: pointer;
}
</style>
<!-- ===================================   block1 ============================== -->	
<div style="position:relative;">

	
	<div style='position:absolute;	bottom:2.5%;right:1.3%;z-index:0;width:36%;'>
		<img class='mySlides animx fishes' src=img/product_slide/v2_cuisinière5.png >
		<img class='mySlides animx fish' src=img/product_slide/v2_cuisinière4.png >
		<img class='mySlides animx fish' src=img/product_slide/v2_cuisinière5.png >
		<img class='mySlides animx fish' src=img/product_slide/v2_cuisinière2.png >
		<img class='mySlides animx fish' src=img/product_slide/v2_cuisinière6.png >
	</div>
	

	<!--
			<img class='mySlides animx fish'   src='img/product_slide/UP6.png' style='opacity:0'>
    -->
	<img id="img_insert" src="img/produit/AP00135_2022_03_23_08_01_27_1648022487.jpg" width="100%" style="margin-top: 20px;z-index=33">

<script>
var x = document.getElementsByClassName("mySlides");
var y=x.length;
setTimeout(carousel1X, 3000);    
function carousel1X() {
if(y==1){
  for (i = 0; i < x.length; i++) {
    x[i].style.opacity = "1";  
  }
  y=x.length;
  setTimeout(carousel1X, 3000);    

}else{
x[y-1].style.opacity = "0";  
y=y-1;
setTimeout(carousel1X, 3000);    
}
}
</script>
<style>
.animx{-webkit-transition: all 1s ;-moz-transition: all 1s ;-o-transition: all 1s ;-ms-transition: all 1s ;transition: all 2s ;}

.mySlides{width:96%;padding:0% 0% 0% 1.9%;cursor:pointer;}
.fishes
	{
		position: relative;
		top: 0;
		left: 0;
	}
	.fish
	{
		position: absolute;
		top: 0px;
		left: 0px;
	}
</style>
</div>






<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->




<!--
<style>
    #titre_footer{
        position:absolute;left:41%;top:18%;width:55%;height:30%;
    }
    #container_footer_liens{
        position:absolute;left:6%;top:59%;
    }
    #container_footer_contact{
        position:absolute;left:20%;top:59%;
    }
    
    .label_contact{
        display:inline-block;
        width:13%;
        font-size:1.2vw;
    }
    .link{font-size:1.2vw;display:inline-block;}
    .link:hover{color:#697fbd;}
    .newsletter{font-size:1.2vw;text-align:justify;line-height: 1.6;}
    li {margin:5px 0px;}
    @media (max-width: 850px){
        h1{margin-bottom:0px;}    
        #titre_footer{top:10%;}
        #lala li{margin:0px 0px;padding:0px;list-style: none;}
        #container_footer_liens{position:absolute;left:5%;top:57%;}
        #container_footer_contact{position:absolute;left:20%;top:57%;}
    }
    
</style>
<div style="position:relative;color:black;">
    <img src="img/BG/newsletter4.png" width="100%" >
    <div id="titre_footer">
            <h1>Newsletter</h1>
            <p class="newsletter">Afin de pouvoir répondre au mieu à la demande de ses clients, Apoint Flamme Bleue à mis en place un système de vente à crédit concernant les chauffages à gaz .
Cette option a été développer dans le but de facilité l'acquisition de ce produit à de nombreuses personnes qui souhaitaient l'acquérir , mais qui avait un soucis pécunier , ou qui souhaitaient tout simplement l'acheter à crédit.
cette formule se présente sous deux formes, à savoir un prêt sur 10 mois ou sur 24 mois.
Notre  marque a commencé  à proposer le chauffage à crédit vu la demande afflue reçue par nos clients, mais nous éspérons pouvoir développer cette formule sur  toute notre gamme de produits. </p>
    </div>
    
    <div id="container_footer_liens">
        <!--
        <ul>
            <li>
                <div class="link"><a href="notre_marque.php">Notre Marque</a></div>
            </li>
            <li>
                <div class="link"><a href="index.php#nos_valeurs">Nos Valeurs</a></div>
            </li>
            <li>
                <div class="link"><a href="nos_produits.php">Nos produits</a></div>
            </li>
            <li>
                <div class="link"><a href="contact.php">Contact</a></div>
            </li>
            <li>
                <div class="link"><a href="sav.php">SAV</a></div>
            </li>

        </ul>
        
        <ul style="width:120%" id="lala">
            <li>
                <div style="margin:5px 0px;"><label class="label_contact">Adresse : </label><div class="link"><a href="contact.php">Zone industrielle Djelfa .lot n 68 16000 Alger, Algérie</a></div></div>
                <div style="margin:5px 0px;"><label class="label_contact"></label><div class="link"><a href="contact.php">06 rue Lakhdar Ben Ferkous, Belouizdad, Alger – Algérie</a></div></div>
                <div style="margin:5px 0px;"><label class="label_contact"></label><div class="link"><a href="contact.php">Coopérative universitaire.Groupe 2. villa N°67. Garidi. Kouba, Alger, Algérie</a></div></div>
            </li>

            <li >
                <div class="link">Contact commercial: <a href="tel:0661 99 27 72">0661 99 27 72</a> / <a href="tel:0555 80 50 21">0555 80 50 21</a></div>
            </li>
            
            <li>
                <div class="link">Contact SAV: <a href="tel:0661 78 76 76">0661 78 76 76</a> / <a href="tel:0560 52 84 15">0560 52 84 15</a></div>
            </li>
            
            
            <li>
                <div class="link"><a href="mailto:contact@apointflammebleue-dz.com">contact@apointflammebleue-dz.com</a></div>
            </li>
            <li>
                <div class="link"><a href="mailto:sav@apointflammebleue-dz.com">sav@apointflammebleue-dz.com</a></div>
            </li>
            
        </ul>
            
            
            
            
            
    </div>
    
    
    <div id="container_footer_contact">
            
            
            
            
            
            
            
            
            
          
    </div>
    
    <div style="position:absolute;left:36%;top:83%;width:30%;">
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/FACEBOOK.png" width="10%"></a>
            <a href="https://www.instagram.com/apointflammebleue2/" target="_blank"><img src="img/icon/INSTA.png" width="10%"></a>
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/MESSENGER.png" width="10%"></a>
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/TWI.png" width="10%"></a>
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/YOUTUBE.png" width="15%"></a>

    
    </div>
    </div>

    
    
    <style>
        .signature{
            text-align:center;
            margin-bottom:50px;
        }
    </style>
    <div class="signature">
        <img src="img/icon/atelier_idée.png" width="30%">
    </div>
-->
<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->
<!-- =================================================== news letters ================================================== -->





<style type="text/css">
.footer_separateur_carre{
    width: 37%;
    height:0px;
    padding-bottom: 39%;
    float:left;
    }

    .footer_main{
        background: url("img/BG/GRAY1.jpg");
        background-repeat: no-repeat;
        background-size: 100% auto;
            }
    .footer_main2{
        background: url("img/BG/GRAY4.png");
        background-repeat: no-repeat;
        background-size: 100% auto;
        background-position: bottom;
            }
    .footer_background{
        background: url("img/BG/GRAY2.jpg");
        background-size: contain;
        color: black;
        font-size: 16px;
            }

    .paragraph_newsletter{
        padding: 8% 5% 1% 5%;

    }

    .paragraph_newsletter p{
        text-align: justify;
        line-height: 1.6;
    }

    .footer_contact{
        padding: 7% 0% 0% 3%;
    }

    .footer_contact div{
        padding: 3px 0px;
    }


    .footer_contact .footer_exception_separation{
        padding-left: 70px;
    }


    .footer_social_media_icons{
        text-align: center;
        padding-top: 5%;
        padding-bottom: 10%;
    }

    .footer_social_media_icons img{
        height: 30px;
        padding: 2px;
    }



    @media (min-width: 1200px){
    
   .paragraph_newsletter{
        padding: 8% 5% 5% 5%;

    }
    }
    @media (max-width: 1200px){
    
    .footer_separateur_carre{
        padding-bottom: 30%;
    }
    }
    @media (max-width: 950px){
    .footer_background{
        font-size: 12px;
        } 
    .footer_contact .footer_exception_separation{
        padding-left: 50px;
    }   

    .footer_contact{
        padding: 2% 0% 0% 3%;
        }        


    } 

@media (max-width: 700px){
    .footer_background{
        font-size: 12px;
        }          



    .footer_contact{
        padding: 0% 0% 0% 3%;
        }

    .footer_social_media_icons{
        padding-left: 3%;
        text-align: left;
        padding-top: 5%;
        padding-bottom: 10%;
    }
    
    .footer_social_media_icons img{
        height: 20px;
    }


    }
</style>

<div class="footer_background">
    <div class="footer_main">
        <div style="width:100%;">
            <div class="paragraph_newsletter">
                <div class="footer_separateur_carre"></div>
                <h1>Newsletter</h1>
                <p>Afin de pouvoir répondre au mieu à la demande de ses clients, Apoint Flamme Bleue à mis en place un système de vente à crédit concernant les chauffages à gaz .
Cette option a été développer dans le but de facilité l'acquisition de ce produit à de nombreuses personnes qui souhaitaient l'acquérir , mais qui avait un soucis pécunier , ou qui souhaitaient tout simplement l'acheter à crédit.
cette formule se présente sous deux formes, à savoir un prêt sur 10 mois ou sur 24 mois.
Notre  marque a commencé  à proposer le chauffage à crédit vu la demande afflue reçue par nos clients, mais nous éspérons pouvoir développer cette formule sur  toute notre gamme de produits. </p>


            </div>
        </div>
    </div>
</div>

<div class="footer_background">
    <div class="footer_main2">
        <div style="width:100%;">
            <div class="footer_contact">
                <div><span>Adresse : </span><a href="contact.php">Zone industrielle Djelfa .lot n 68 16000 Alger, Algérie</a></div>
                <div class="footer_exception_separation"><a href="contact.php">06 rue Lakhdar Ben Ferkous, Belouizdad, Alger – Algérie</a></div>
                <div class="footer_exception_separation"><a href="contact.php">Coopérative universitaire.Groupe 2. villa N°67. Garidi. Kouba, Alger, Algérie</a></div>
                <div>Contact commercial: <a href="tel:0661 99 27 72">0661 99 27 72</a> / <a href="tel:0555 80 50 21">0555 80 50 21</a></div>
                <div>Contact SAV: <a href="tel:0661 78 76 76">0661 78 76 76</a> / <a href="tel:0560 52 84 15">0560 52 84 15</a></div>
                <div><a href="mailto:contact@apointflammebleue-dz.com">contact@apointflammebleue-dz.com</a></div>
                <div><a href="mailto:sav@apointflammebleue-dz.com">sav@apointflammebleue-dz.com</a></div>
            </div>

        </div>



        <div class="footer_social_media_icons">
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/FACEBOOK.png"></a>
            <a href="https://www.instagram.com/apointflammebleue2/" target="_blank"><img src="img/icon/INSTA.png"></a>
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/MESSENGER.png"></a>
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/TWI.png"></a>
            <a href="https://web.facebook.com/Apoint.flamme.bleue1" target="_blank"><img src="img/icon/YOUTUBE.png"></a>
        </div>
    
    </div>
</div>


    <style>
        .signature{
            text-align:center;
            margin-bottom:50px;
            background: white;
            margin-top: -3px;
        }
    </style>
    <div class="signature">
        <img src="img/icon/atelier_idée.png" width="30%">
    </div>









        


</body>









































