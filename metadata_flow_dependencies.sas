
/***********************************************************************************/
/* Makro rekurencyjne do odkrywania wszystkich obiektow w flow i subflow.          */
/***********************************************************************************/
%macro discover_all_objects(flow_uri);
    %macro kolor; %mend kolor;


    /* Pobierz URI kolekcji 'JobActivities', ktora grupuje kroki w danym flow */
    data _null_;
        length rc 8 job_act_uri $256;               
        rc = metadata_getnasn("&flow_uri", "JobActivities", 1, job_act_uri);
        if rc > 0 then call symputx('current_job_act_uri', job_act_uri);
        else call symputx('current_job_act_uri', '');
    run;

    /* Jesli flow zawiera jakiekolwiek kroki (JobActivities), przetwarzaj je */
    %if %length(&current_job_act_uri) > 0 %then %do;

        /* Utworz tymczasowa tabele na obiekty znalezione na tym poziomie zagniezdzenia */
        data _objects_at_this_level_(keep=id name type uri flow_uri flow_name transform_role transform_uri dir_uri file_uri code_file_name code_dir_name);
            length rc 8 n_step 8 rc_trans 8 rc_id rc_role rc_f 8 rc_sc rc_fn rc_d rc_dn 8
                   uri $256 id $50 name $100 type $50
                   transform_uri $256 depend_uri $256 transform_role $50
                   flow_uri file_uri dir_uri $256 flow_name code_file_name $100 code_dir_name $256;
            
            call missing(of _character_);

            flow_uri = "&flow_uri"; /* Zapamietaj URI biezacego flow */
            rc_f = metadata_getattr(flow_uri, "Name", flow_name);
            
            rc = 1; 
            n_step = 1;
            /* Petla po wszystkich krokach ('Steps') wewnatrz 'JobActivities' */
            do while(rc > 0);
                rc = metadata_getnasn("&current_job_act_uri", "Steps", n_step, uri);
                
                if rc > 0 then do;
                    
                    
                    /* Pobierz podstawowe atrybuty kroku */
                    rc_id = metadata_getattr(uri, "Id", ID);
                    rc_role = metadata_getattr(uri, "TransformRole", transform_role);


                    /* Sprawdz, czy krok jest powiazany z transformacja (np. Job, Subflow) */
                    rc_trans = metadata_getnasn(uri, "Transformations", 1, transform_uri);

                    rc_sc = metadata_getnasn(transform_uri,"SourceCode",1,file_uri);
                	rc_fn = metadata_getattr(file_uri,"FileName",code_file_name);
                	rc_d = metadata_getnasn(file_uri,"Directories",1,dir_uri);
                	rc_dn = metadata_getattr(dir_uri,"DirectoryName",code_dir_name);

                    
                    if rc_trans > 0 then do;
                       /* Jesli tak, pobierz jej typ (PublicType) i nazwe (Name) */
                       rc_pubtype = metadata_getattr(transform_uri, "PublicType", type);
                       rc_name = metadata_getattr(transform_uri, "Name", name);
                       
                    end;
                    else do;
                       /* Jesli nie ma transformacji, to jest to obiekt logiczny (bramka, zdarzenie) */
                       /* Jego typem jest rola, a nazwe tworzymy z roli i ID */
                       type = transform_role;
                       name = cats(transform_role, '_', ID);
                    end;
                    
                    output;
                end;
                n_step + 1;
            end;
        run;
        
        /* Dolacz obiekty z tego poziomu do glownej tabeli wynikowej */
        proc append base=all_flow_objects_tmp data=_objects_at_this_level_ force; 
        run;

        /* Uruchom rekurencje dla znalezionych subflow */
        data _null_;
            set _objects_at_this_level_;
            /* 'TransformationFlow' i 'DeployedFlow' to typy publiczne dla subflow */
            if TYPE = 'DeployedFlow' then do;
                /* Wywolaj to samo makro dla URI znalezionego subflow */
                call execute(cats('%nrstr(%discover_all_objects(flow_uri=', transform_uri, '))'));
            end;
        run;
    %end;


%mend discover_all_objects;



%macro get_flow_objects(flow_name);
    %macro kolor; %mend kolor;

    %let max_iter = 20;

    /* Czyszczenie tabel roboczych z poprzednich uruchomien */
    proc datasets lib=work nolist nowarn;
        delete all_flow_objects_tmp all_flow_objects _objects_at_this_level_ job_successors successors predecessors;
    quit;

    /* Utworzenie pustej tabeli wynikowej ze zdefiniowana struktura */
    data all_flow_objects;
        length ID $50 NAME $100 TYPE $50 FLOW_NAME $100 TRANSFORM_ROLE $50 CODE_DIR_NAME $256 CODE_FILE_NAME $100;
        stop;
    run;

    data predecessors;
        length ID $50 NAME $100 PREV_ID $50 PREV_NAME $100 FLOW_NAME $100;
        stop;
    run;

    data successors;
        length ID $50 NAME $100 NEXT_ID $50 NEXT_NAME $100 FLOW_NAME $100;
        stop;
    run;

    data job_successors;
        length ID $50 NAME $100 NEXT_ID $50 NEXT_NAME $100;
        stop;
    run;
    
    /* Odszukaj URI flow najwyzszego poziomu na podstawie jego nazwy */
    data _null_;
        length nobj 8 top_flow_uri $256; 
        nobj = metadata_getnobj("omsobj:transformation?@Name eq '" || strip("&flow_name") || "'", 1, top_flow_uri);
        if nobj > 0 then call symputx("top_flow_uri", top_flow_uri);
        else put "BLAD: Nie znaleziono przeplywu o nazwie &flow_name";
    run;

    /* Jesli flow zostal znaleziony, rozpocznij proces odkrywania obiektow */
    %if %symexist(top_flow_uri) %then %do;
        
        %put NOTE: Rozpoczynam przetwarzanie flow: &flow_name (URI: &top_flow_uri);

        %discover_all_objects(flow_uri=&top_flow_uri);

        proc append base=all_flow_objects data=all_flow_objects_tmp force;
        run;

        data successors_tmp(keep=id name next_id next_name flow_name);
            length dep_uri next_uri $256 next_name $100  next_id transform_role $50;
            call missing(dep_uri, next_uri, next_id, next_name, transform_role );

            set all_flow_objects_tmp;

            n = 1; rc_dep = 1;
            do while(rc_dep > 0);
        	    rc_dep = metadata_getnasn(uri, "SuccessorDependencies", n, dep_uri);
        	    rc_next = metadata_getnasn(dep_uri, "Predecessors", 1, next_uri);
                rc = metadata_getattr(next_uri, "Id", next_id);
                rc = metadata_getattr(next_uri, "Name", next_name);
                rc_role = metadata_getattr(next_uri, "TransformRole", transform_role);
                if transform_role in ('AND' 'OR') then next_name = cats(transform_role,'_',next_id);
                output; 
                n + 1;
            end;

        run;

        proc sort data=successors_tmp nodupkey;
            by _all_;
        run;

        proc append base=successors data=successors_tmp;
        run;

        data predecessors_tmp(keep=id name prev_id prev_name flow_name);
            length dep_uri prev_uri $256  prev_name $100 prev_id $50;
            call missing(dep_uri, prev_uri, prev_id, prev_name );

            set all_flow_objects_tmp;

            n = 1; rc_dep = 1;
            do while(rc_dep > 0);
                rc_dep = metadata_getnasn(uri, "PredecessorDependencies", n, dep_uri);
                rc_prev = metadata_getnasn(dep_uri, "Successors", 1, prev_uri);
                rc = metadata_getattr(prev_uri, "Id", prev_id);
                rc = metadata_getattr(prev_uri, "Name", prev_name);
                rc_role = metadata_getattr(next_uri, "TransformRole", transform_role);
                if transform_role in ('AND' 'OR') then prev_name = cats(transform_role,'_',prev_id);
                output;
                n + 1;
            end;

        run;

        proc sort data=predecessors_tmp nodupkey;
            by _all_;
        run;

        proc append base=predecessors data=predecessors_tmp;
        run;



    %end;


    /* KROK 1: Stworz poczatkowa, kompletna tabele polaczen */
    proc sql noprint;
        CREATE TABLE links AS
        SELECT
            p.id, 
            p.name, 
            p.type, p.flow_name,
            n.next_id, 
            s.name AS next_name, 
            s.type AS type_next, 
            s.flow_name AS flow_name_next
        FROM 
            successors AS n
        INNER JOIN 
            all_flow_objects AS p 
        ON 
            n.id = p.id
        INNER JOIN 
            all_flow_objects AS s 
        ON 
            n.next_id = s.id;
    quit;
    
    /* KROK 2: Iteracyjnie rozwiazuj polaczenia posrednie */
    %do i = 1 %to &max_iter;
        %put NOTE: Iteracja rozwiazywania nr &i....;
        
        proc sql noprint;
            SELECT count(*) INTO :obs_before trimmed FROM links;
        quit;

        proc sql;
            CREATE TABLE links_iter AS
            
            /* REGULA 1: Zachowaj wszystkie istniejace polaczenia, ktore sa juz bezposrednie (Job -> Job) */
            SELECT * 
            FROM 
                links
            WHERE 
                Type = 'DeployedJob' AND type_next = 'DeployedJob'

            UNION

            /* REGULA 2: Rozwiaz kontenery (Flows) jako nastepnikow (A -> Flow) */
            SELECT 
                l.id, 
                l.name, 
                l.type, 
                l.flow_name,
                entry_points.id, 
                entry_points.name, 
                entry_points.type, 
                entry_points.flow_name
            FROM 
                links l
            INNER JOIN 
                all_flow_objects as entry_points 
            ON 
                l.next_name = entry_points.flow_name
            WHERE 
                l.type_next = 'DeployedFlow'
            AND NOT EXISTS (SELECT 1 
                            FROM 
                                predecessors p 
                            INNER JOIN 
                                all_flow_objects o ON p.prev_id=o.id
                            WHERE 
                                p.id = entry_points.id AND o.flow_name = entry_points.flow_name
                            )

            UNION

            /* REGULA 3: Rozwiaz kontenery (Flows) jako poprzednikow (Flow -> C) */
            SELECT 
                exit_points.id, 
                exit_points.name, 
                exit_points.type, 
                exit_points.flow_name,
                l.next_id, 
                l.next_name, 
                l.type_next, 
                l.flow_name_next
            FROM 
                links l
            INNER JOIN 
                all_flow_objects AS exit_points 
            ON 
                l.name = exit_points.flow_name
            WHERE 
                l.Type = 'DeployedFlow'
            aND NOT EXISTS (SELECT 1 
                            FROM 
                                successors n 
                            INNER JOIN 
                                all_flow_objects o 
                            ON n.next_id=o.id
                            WHERE 
                                n.id = exit_points.id AND o.flow_name = exit_points.flow_name
                            )
            
            UNION

            /* REGULA 4: Rozwiaz wezly przelotowe (Bramki) tworzac skroty A->C dla sciezek A->Bramka->C */
            SELECT 
                a.id, 
                a.name, 
                a.type, 
                a.flow_name,
                c.next_id, 
                c.next_name, 
                c.type_next, 
                c.flow_name_next
            FROM 
                links a
            INNER JOIN 
                links c on a.next_id = c.id
            WHERE 
                a.type_next IN ('AND', 'OR');
        quit;
        
        proc datasets lib=work nolist;
            delete links;
            change links_iter=links;
        quit;
        
        proc sort data=links out=links_dedup nodupkey;
            by _all_;
        run;
        
        proc datasets lib=work nolist;
            delete links;
            change links_dedup=links;
        quit;
        
        proc sql noprint;
            select count(*) into :obs_after trimmed from links;
        quit;
        
        %if &obs_after = &obs_before %then %do;
            %put NOTE: Osiagnieto zbieznosc. Koniec iteracji.;
            %goto end_loop;
        %end;
    %end;
    %end_loop:


    proc sql;
        CREATE TABLE job_successors_tmp AS
        SELECT DISTINCT 
            id, 
            name, 
            next_id, 
            next_name
        FROM 
            links
        WHERE 
            type = 'DeployedJob' and type_next = 'DeployedJob'
        ORDER BY 
            name, next_name;
    quit;

    proc append base = job_successors data =  job_successors_tmp force;
    run;

    proc datasets lib=work nolist nowarn;
        delete job_successors_tmp _objects_at_this_level_ links predecessors_tmp successors_tmp all_flow_objects_tmp;
    quit;

%mend get_flow_objects;


%get_flow_objects(flow_name=X_Flow);


%let container_path = /mishome/rafsul033000/python/flow_runner_project/;


proc sql;
    CREATE TABLE flow_dependencies AS
    SELECT
        t1.id,
        t1.name,
        t2.code_file_name,
        t1.next_id,
        t1.next_name,
        t3.code_file_name AS NEXT_CODE_FILE_NAME
    FROM
        job_successors t1
    LEFT JOIN
        all_flow_objects t2
    ON
        t1.id = t2.id
    LEFT JOIN
        all_flow_objects t3
    ON
        t1.next_id = t3.id      
    ;
quit;

proc export data=flow_dependencies 
     outfile="&container_path./data/flow_dependencies.csv"
     dbms=csv
     replace;
     delimiter=';';
run;


